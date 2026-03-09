# nutrition_coach

## Release

To release a new version, you can use automatic `release` command
installed by `devenv` scripts. This script will:

1. Bump the version based on [Conventional
Commits](https://www.conventionalcommits.org/en/v1.0.0/) format found
in the commit history.
2. Update `CHANGELOG.MD`.
3. Assign version tag to the repository.

After the script finished successfully, you need to:

1. Commit changes.
2. `git push` and `git push --tags`.

If you want to have a release on your source control system, Github or
Gitlab, you can do it dependent to the system, using the published
tags.


## Running the MyFitnessPal API Server

### Installation

Install the project dependencies using Poetry:

```bash
poetry install
```

### Running the Server

You can run the API server using either of the following commands:

```bash
python src/nutrition_coach/api_server.py
```

Or, if you prefer to run it within the Poetry environment directly:

```bash
poetry run python src/nutrition_coach/api_server.py
```

The server will start on `http://localhost:5000` by default.

### Querying the API

You can query the API by sending a GET request to the appropriate endpoint. For example, to get the diary for May 27, 2023:

Using `curl`:
```bash
curl http://localhost:5000/diary/2023/05/27
```

Or by visiting the URL in your web browser:
`http://localhost:5000/diary/2023/05/27`

### Cookie Management and Authentication

The server uses the `browser-cookie3` library to automatically load authentication cookies from your web browser(s) (e.g., Chrome, Firefox) where you are logged into MyFitnessPal.

You do **not** need to manage a separate cookie file or volume for this application. `browser-cookie3` reads directly from the browser's standard cookie storage locations on the machine where the server is running.

To 'update' or ensure the cookies are fresh, simply make sure you are actively logged into your MyFitnessPal account in one of the supported browsers on the same machine. The application will attempt to load the latest available cookies each time it initializes the MyFitnessPal client (i.e., on each API request that requires fetching data).

If cookies cannot be loaded (e.g., you are not logged in, or the browser is not supported/found), the API will return an error.
