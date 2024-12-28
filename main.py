import typer

#import serverclass
import sessionkey

app = typer.Typer()

app.add_typer(sessionkey.app, name="sessionkey")
#app.add_typer(serverclass.app, name="serverclass")

if __name__ == "__main__":
    app()