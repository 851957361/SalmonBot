import salmon


salmon.init()
app = salmon.asgi()

if __name__ == "__main__":
    salmon.run('run:app')