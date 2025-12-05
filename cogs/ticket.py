import discord
from discord.ext import commands
from discord.ui import View, Button
from utils.helpers import load_config, save_config
import datetime
import io

# 🔒 HARD LOCKED IDS
PANEL_AND_CREATE_CHANNEL_ID = 1396049500744847360
PANEL_PAYMENT_PROOF_CHANNEL_ID = 1402658392966696990
PAYMENT_PROOF_CHANNEL_ID = 1417833322889085070
PAYMENT_METHODS_CHANNEL_ID = 1443795686255628360

SUPPORT_ROLE_NAME = "Support Team"

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= SETUP =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        guild = ctx.guild

        category = discord.utils.get(guild.categories, name="🎫 Tickets")
        if not category:
            category = await guild.create_category("🎫 Tickets")

        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        if not support_role:
            support_role = await guild.create_role(name=SUPPORT_ROLE_NAME)

        data = load_config()
        data[str(guild.id)] = {
            "category": category.id,
            "support_role": support_role.id
        }
        save_config(data)

        await ctx.send("✅ Ultra Professional Ticket System Setup Complete!")

    # ================= PANEL =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sendpanel(self, ctx):
        panel_channel = self.bot.get_channel(PANEL_AND_CREATE_CHANNEL_ID)
        data = load_config().get(str(ctx.guild.id))

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

        view = View(timeout=None)

        async def open_ticket(interaction):
            if interaction.channel.id != PANEL_AND_CREATE_CHANNEL_ID:
                return await interaction.response.send_message(
                    "❌ Ticket sirf official panel se open hota hai!", ephemeral=True
                )

            guild = interaction.guild
            config = load_config()[str(guild.id)]
            category = guild.get_channel(config["category"])
            support_role = guild.get_role(config["support_role"])

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
                support_role: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites
            )

            await channel.send(
                f"✅ Welcome {interaction.user.mention}\n"
                "🛒 ID / Panel / Bulk / Reseller\n"
                f"💳 Payment: <#{PAYMENT_METHODS_CHANNEL_ID}>"
            )

            await interaction.response.send_message("🎫 Ticket Created!", ephemeral=True)

        btn = Button(label="🎫 Open Ticket", style=discord.ButtonStyle.green)
        btn.callback = open_ticket
        view.add_item(btn)

        await panel_channel.send(embed=embed, view=view)
        await ctx.send("✅ Panel Sent Successfully!")

    # ================= STAFF ONLY =================
    def staff_only():
        async def predicate(ctx):
            data = load_config().get(str(ctx.guild.id))
            role = ctx.guild.get_role(data["support_role"])
            return role in ctx.author.roles
        return commands.check(predicate)

    @commands.command()
    @staff_only()
    async def claim(self, ctx):
        await ctx.send(f"✅ Ticket Claimed by {ctx.author.mention}")

    @commands.command()
    @staff_only()
    async def rename(self, ctx, *, name):
        await ctx.channel.edit(name=name)
        await ctx.send("✅ Ticket Renamed")

    @commands.command()
    @staff_only()
    async def add(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(f"✅ {member.mention} added")

    @commands.command()
    @staff_only()
    async def remove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"✅ {member.mention} removed")

    @commands.command()
    @staff_only()
    async def priority(self, ctx):
        await ctx.channel.edit(name="🔥-priority-ticket")
        await ctx.send("✅ Priority Ticket Marked")

    @commands.command()
    @staff_only()
    async def transfer(self, ctx, member: discord.Member):
        await ctx.send(f"✅ Ticket Transferred to {member.mention}")

    # ================= TRANSCRIPT =================
    @commands.command()
    @staff_only()
    async def transcript(self, ctx):
        messages = []
        async for msg in ctx.channel.history(limit=200):
            messages.append(f"{msg.author}: {msg.content}")

        text = "\n".join(reversed(messages))
        file = discord.File(io.BytesIO(text.encode()), filename="transcript.txt")
        await ctx.send(file=file)

    # ================= SELLER COMMANDS =================
    @commands.command()
    async def price(self, ctx):
        await ctx.send("💰 Price List: 100rs - 10k")

    @commands.command()
    async def stock(self, ctx):
        await ctx.send("📦 Stock Available ✅")

    @commands.command()
    async def upi(self, ctx):
        await ctx.send("💳 UPI ID: digamber@upi")

    @commands.command()
    async def reseller(self, ctx):
        await ctx.send("👑 Reseller Plan Available – DM Staff")

    @commands.command()
    async def verify(self, ctx):
        await ctx.send("✅ Payment Verify in Progress...")

    # ================= CLOSE =================
    @commands.command()
    @staff_only()
    async def close(self, ctx):
        await ctx.send("🔒 Closing ticket in 5 seconds...")
        await ctx.channel.delete(delay=5)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
