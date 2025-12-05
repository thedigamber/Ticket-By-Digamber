import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from utils.helpers import load_config, save_config
import io
import asyncio
import datetime

# ---------------------------
# HARD-LOCKED CHANNEL IDS
# ---------------------------
PANEL_AND_CREATE_CHANNEL_ID = 1396049500744847360
PANEL_PAYMENT_PROOF_CHANNEL_ID = 1402658392966696990
PAYMENT_PROOF_CHANNEL_ID = 1417833322889085070
PAYMENT_METHODS_CHANNEL_ID = 1443486183928889416

# ---------------------------
# NAMES (from user)
# ---------------------------
SUPPORT_ROLE_NAME = "Tickets Access"
TICKET_CATEGORY_NAME = "Tickets System"
LOG_CHANNEL_NAME = "Ticket-Logs"

# ---------------------------
# Cog
# ---------------------------
class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------
    # Helper: staff-only check decorator
    # ---------------------------
    def staff_only():
        async def predicate(interaction_or_ctx):
            # supports both Context and Interaction
            guild = interaction_or_ctx.guild if hasattr(interaction_or_ctx, "guild") else None
            if guild is None:
                return False
            data = load_config().get(str(guild.id), {})
            role_id = data.get("support_role")
            if not role_id:
                return False
            role = guild.get_role(role_id)
            member = interaction_or_ctx.author if hasattr(interaction_or_ctx, "author") else interaction_or_ctx.user
            return role in member.roles
        return commands.check(predicate)

    # ---------------------------
    # SETUP - hybrid (prefix + slash)
    # Creates category, support role, log channel and saves config
    # ---------------------------
    @commands.hybrid_command(name="setup", description="Auto-setup ticket category, support role and logs")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx: commands.Context):
        guild = ctx.guild
        data = load_config()

        # Create category
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        # Create support role
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        if not support_role:
            support_role = await guild.create_role(name=SUPPORT_ROLE_NAME)
            # give view_channel by default to role will be applied per ticket

        # Create 'Ticket-Logs' channel (if not exists)
        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if not log_channel:
            log_channel = await guild.create_text_channel(LOG_CHANNEL_NAME)

        # Save config
        data[str(guild.id)] = {
            "category": category.id,
            "support_role": support_role.id,
            "log_channel": log_channel.id
        }
        save_config(data)

        await ctx.send(f"✅ Ultra Setup Complete!\nCategory: `{category.name}`\nSupport Role: `{support_role.name}`\nLog Channel: `{log_channel.name}`")

    # ---------------------------
    # SEND PANEL (only admin) - hybrid
    # Panel is always sent to hard-coded PANEL_AND_CREATE_CHANNEL_ID
    # ---------------------------
    @commands.hybrid_command(name="sendpanel", description="Send official ticket panel to the locked panel channel")
    @commands.has_permissions(administrator=True)
    async def sendpanel(self, ctx: commands.Context):
        panel_channel = self.bot.get_channel(PANEL_AND_CREATE_CHANNEL_ID)
        guild = ctx.guild
        if not panel_channel:
            return await ctx.send("❌ Panel channel not found or bot doesn't have access.")

        data = load_config().get(str(guild.id))
        if not data:
            return await ctx.send("❌ Please run `!setup` first.")

        embed = discord.Embed(
            title="🎟️ Free Fire ID & Panel Support",
            description=(
                "🔥 **Official Digamber Free Fire Store**\n\n"
                f"💳 Payment Methods: <#{PAYMENT_METHODS_CHANNEL_ID}>\n"
                f"📊 Panel Proofs: <#{PANEL_PAYMENT_PROOF_CHANNEL_ID}>\n"
                f"✅ Payment Proofs: <#{PAYMENT_PROOF_CHANNEL_ID}>\n\n"
                "👇 Ticket open karne ke liye button dabaye 👇"
            ),
            color=0x00ffcc
        )
        embed.set_footer(text="Powered by Digamber | 100% Trusted Seller")

        view = View(timeout=None)

        async def open_ticket(interaction: discord.Interaction):
            # Ensure only from panel channel
            if interaction.channel.id != PANEL_AND_CREATE_CHANNEL_ID:
                return await interaction.response.send_message("❌ Ticket sirf official panel se open hota hai!", ephemeral=True)

            guild = interaction.guild
            cfg = load_config().get(str(guild.id))
            if not cfg:
                return await interaction.response.send_message("❌ Server not configured. Ask an admin to run !setup.", ephemeral=True)

            category = guild.get_channel(cfg["category"])
            support_role = guild.get_role(cfg["support_role"])

            # Build overwrites
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # create unique channel name
            safe_name = interaction.user.name.lower().replace(" ", "-")[:20]
            channel_name = f"ticket-{safe_name}"

            # Create channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )

            # Send welcome embed
            welcome = discord.Embed(
                title="✅ Welcome to your Ticket",
                description=(
                    f"{interaction.user.mention}, team will contact you here.\n\n"
                    "🛒 **Aap kya purchase karna chahte ho?**\n"
                    "• Free Fire ID\n• Panel\n• Bulk IDs\n• Reseller Deal\n\n"
                    f"💳 Payment Methods: <#{PAYMENT_METHODS_CHANNEL_ID}>\n"
                    f"✅ Payment Proofs: <#{PAYMENT_PROOF_CHANNEL_ID}>\n\n"
                    "⚠️ Fake proofs = direct ban\n"
                ),
                color=0x009688
            )
            await ticket_channel.send(embed=welcome)

            # notify user ephemeral
            await interaction.response.send_message("🎫 Ticket successfully created! Check the new channel.", ephemeral=True)

            # log creation
            log = guild.get_channel(cfg.get("log_channel"))
            if log:
                await log.send(f"🆕 Ticket created: {ticket_channel.mention} by {interaction.user.mention}")

        btn = Button(label="🎫 Open Ticket", style=discord.ButtonStyle.success)
        btn.callback = open_ticket
        view.add_item(btn)

        await panel_channel.send(embed=embed, view=view)
        await ctx.send("✅ Panel sent to the official panel channel.")

    # ---------------------------
    # Staff-only helper for commands (decorator for commands.check)
    # ---------------------------
    def _staff_check(ctx):
        data = load_config().get(str(ctx.guild.id), {})
        role_id = data.get("support_role")
        if not role_id:
            return False
        role = ctx.guild.get_role(role_id)
        return role in ctx.author.roles

    # ---------------------------
    # STAFF COMMANDS (hybrid)
    # ---------------------------
    @commands.hybrid_command(name="claim", description="Claim this ticket")
    @commands.check(_staff_check)
    async def claim(self, ctx):
        await ctx.send(f"✅ {ctx.author.mention} has claimed this ticket.")

    @commands.hybrid_command(name="rename", description="Rename the ticket channel")
    @commands.check(_staff_check)
    async def rename(self, ctx, *, name: str):
        await ctx.channel.edit(name=name)
        await ctx.send(f"✅ Ticket renamed to `{name}`")

    @commands.hybrid_command(name="add", description="Add a member to the ticket")
    @commands.check(_staff_check)
    async def add(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(f"✅ {member.mention} added to the ticket.")

    @commands.hybrid_command(name="remove", description="Remove a member from the ticket")
    @commands.check(_staff_check)
    async def remove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"✅ {member.mention} removed from the ticket.")

    @commands.hybrid_command(name="priority", description="Mark ticket as priority")
    @commands.check(_staff_check)
    async def priority(self, ctx):
        new_name = f"🔥-{ctx.channel.name}"
        await ctx.channel.edit(name=new_name[:100])
        await ctx.send("✅ Ticket marked as priority.")

    @commands.hybrid_command(name="transfer", description="Transfer ticket to another staff")
    @commands.check(_staff_check)
    async def transfer(self, ctx, member: discord.Member):
        await ctx.send(f"✅ Ticket assigned/transfer requested to {member.mention}")

    # ---------------------------
    # TRANSCRIPT
    # ---------------------------
    @commands.hybrid_command(name="transcript", description="Export a transcript of this ticket")
    @commands.check(_staff_check)
    async def transcript(self, ctx):
        messages = []
        async for m in ctx.channel.history(limit=1000, oldest_first=True):
            time = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = m.author
            content = m.content or ""
            messages.append(f"[{time}] {author} : {content}")
        text = "\n".join(messages)
        fp = io.BytesIO(text.encode("utf-8"))
        file = discord.File(fp, filename=f"transcript-{ctx.channel.name}.txt")
        # send to logs
        data = load_config().get(str(ctx.guild.id), {})
        log_channel = ctx.guild.get_channel(data.get("log_channel"))
        if log_channel:
            await log_channel.send(f"📄 Transcript for {ctx.channel.mention}", file=file)
            await ctx.send("✅ Transcript saved to logs.")
        else:
            await ctx.send(file=file)

    # ---------------------------
    # Seller Commands
    # ---------------------------
    @commands.hybrid_command(name="price", description="Show price list")
    async def price(self, ctx):
        embed = discord.Embed(title="💰 Price List", description="1️⃣ 10k - ₹100\n2️⃣ 50k - ₹400\nContact staff for custom orders.", color=0x2ecc71)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stock", description="Show stock")
    async def stock(self, ctx):
        await ctx.send("📦 Stock Available ✅")

    @commands.hybrid_command(name="upi", description="Show UPI ID")
    async def upi(self, ctx):
        await ctx.send("💳 UPI: `digamber@upi`")

    @commands.hybrid_command(name="reseller", description="Reseller info")
    async def reseller(self, ctx):
        await ctx.send("👑 Reseller plan available. DM staff for details.")

    @commands.hybrid_command(name="verify", description="Mark payment verified (staff use)")
    @commands.check(_staff_check)
    async def verify(self, ctx):
        await ctx.send("✅ Payment verified. Please ask the user to post proof in the payment-proof channel.")

    # ---------------------------
    # CLOSE command: staff only.
    # On close -> create transcript, ask for feedback (1-5), log rating, then delete channel.
    # ---------------------------
    @commands.hybrid_command(name="close", description="Close this ticket (staff only)")
    @commands.check(_staff_check)
    async def close(self, ctx):
        # ensure this is a ticket channel
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.send("❌ This is not a ticket channel.")

        guild = ctx.guild
        cfg = load_config().get(str(guild.id), {})
        log_channel = guild.get_channel(cfg.get("log_channel"))

        # 1) transcript
        messages = []
        async for m in ctx.channel.history(limit=1000, oldest_first=True):
            time = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = m.author
            content = m.content or ""
            messages.append(f"[{time}] {author}: {content}")
        transcript_text = "\n".join(messages)
        transcript_file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"transcript-{ctx.channel.name}.txt")

        if log_channel:
            await log_channel.send(f"🔒 Ticket closed: {ctx.channel.name} by {ctx.author.mention}", file=transcript_file)
        else:
            # fallback: attach to current channel before delete
            await ctx.send(file=transcript_file)

        # 2) feedback view (buttons 1-5)
        class FeedbackView(View):
            def __init__(self, author):
                super().__init__(timeout=60)
                self.author = author
                self.given = False

            async def on_timeout(self):
                # if no feedback given in 60s, proceed delete will continue
                pass

            async def record(self, interaction: discord.Interaction, rating: int):
                if self.given:
                    return await interaction.response.send_message("You already submitted feedback.", ephemeral=True)
                self.given = True
                user = interaction.user
                # only ticket author or staff can rate — allow author or any staff
                ticket_owner = None
                async for m in ctx.channel.history(limit=200):
                    # find earliest non-bot user as owner fallback
                    if not m.author.bot:
                        ticket_owner = m.author
                        break
                # log rating
                rating_msg = f"⭐ Rating: {rating} by {user.mention} for {ctx.channel.name}"
                if log_channel:
                    await log_channel.send(rating_msg)
                await interaction.response.send_message(f"Thanks! You rated {rating} star(s).", ephemeral=True)
                # after rating, delete channel in 5s
                await asyncio.sleep(2)
                try:
                    await ctx.channel.delete()
                except Exception:
                    pass

            @discord.ui.button(label="1", style=discord.ButtonStyle.gray)
            async def one(self, interaction: discord.Interaction, button: Button):
                await self.record(interaction, 1)

            @discord.ui.button(label="2", style=discord.ButtonStyle.gray)
            async def two(self, interaction: discord.Interaction, button: Button):
                await self.record(interaction, 2)

            @discord.ui.button(label="3", style=discord.ButtonStyle.gray)
            async def three(self, interaction: discord.Interaction, button: Button):
                await self.record(interaction, 3)

            @discord.ui.button(label="4", style=discord.ButtonStyle.gray)
            async def four(self, interaction: discord.Interaction, button: Button):
                await self.record(interaction, 4)

            @discord.ui.button(label="5", style=discord.ButtonStyle.green)
            async def five(self, interaction: discord.Interaction, button: Button):
                await self.record(interaction, 5)

        # send feedback prompt in ticket channel
        try:
            await ctx.send("🔔 Ticket will be closed. Please give your feedback (1-5):", view=FeedbackView(ctx.author))
        except Exception:
            # if cannot send view, just delete
            try:
                await ctx.channel.delete()
            except Exception:
                pass

    # ---------------------------
    # Cog setup
    # ---------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
    print("✅ Ticket cog loaded.")
