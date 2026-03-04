"""Entry point: python -m tui"""

from tui.app import MyAIGameApp


def main():
    app = MyAIGameApp()
    app.run()


if __name__ == "__main__":
    main()
