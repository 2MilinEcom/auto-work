# Auto Work

I built Auto Work to keep the different parts of a job search together. I can track applications, prepare for interviews, organize scheduling plans, and review reply drafts without switching between separate spreadsheets.

I included separate personal and fictional demo workspaces, local backup and restore, and optional imports from Gmail and Calendar. The local app uses rules and templates for preparation. It does not send emails or submit applications.

## Built with

I used Python for the local server and JavaScript for the interface and worker.

## Inside the project

* `server.py`: the local server and import bridge.
* `dist/`: the interface served by the local app.
* `worker/`: the hosted worker implementation.
* `tests/`: server and workflow checks.

## Running it

I start the local app with `python3 server.py` and open `http://localhost:8787`. Python 3.10 or later is required. I use Explore demo to try it with fictional information.

## More detail

* [Project guide](PROJECT_GUIDE.md)
* [Optional Google setup](docs/GOOGLE_SETUP.md)
* [Worker setup](docs/AUTOMATION.md)
