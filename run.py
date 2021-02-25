import salmon

bot = salmon.init()
app = bot.get_asgi()

if __name__ == "__main__":
    bot.run()