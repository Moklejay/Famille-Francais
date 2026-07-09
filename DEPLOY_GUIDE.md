# Getting this onto your sister's iPhone -- the easy way

This app is a Python web app, which means it can't be "installed" as an
iPhone app the normal way. But we can put it on the free web at a private
link -- then your sister just taps the link in Safari, like visiting any
website. No App Store, no install, nothing for her to set up at all. You
do a one-time setup (about 10-15 minutes), all free.

You only need to do this **once**. After that, both of you just open the
same link, forever (until you want to change the code).

No terminal, no coding, no command line needed anywhere below -- everything
is clicking buttons on websites.

---

## Step 1 -- Get the files ready

1. Download `famille_francais_ai.zip` (the file I gave you) and unzip it
   on your computer. You'll get a folder called `famille_francais`
   containing `app.py`, a `core` folder, a `pages` folder, etc.

---

## Step 2 -- Put the files on GitHub (free file host that Streamlit reads from)

1. Go to [github.com](https://github.com) and click **Sign up** (skip if
   you already have an account).
2. Once logged in, click the **+** icon top-right -> **New repository**.
3. Name it anything, e.g. `famille-francais`. Leave it **Public** or
   **Private** (either works). Click **Create repository**.
4. On the new repo's page, click **"uploading an existing file"** (a blue
   link in the middle of the page).
5. Open the unzipped `famille_francais` folder on your computer, select
   **everything inside it** -- `app.py`, the `core` folder, the `pages`
   folder, the `data` folder, `requirements.txt`, `README.md`,
   `.gitignore`, `DEPLOY_GUIDE.md` -- and drag all of it into the browser
   upload box. (Make sure you drag what's *inside* the folder, not the
   `famille_francais` folder itself -- `app.py` should end up sitting at
   the top level of the repo.)
6. Scroll down, click the green **Commit changes** button. Wait for the
   upload to finish.

---

## Step 3 -- Deploy it on Streamlit Community Cloud (this gives you the link)

1. Go to [share.streamlit.io](https://share.streamlit.io) and click
   **Sign up** / **Continue with GitHub** -- log in with the same GitHub
   account from Step 2.
2. Click **Create app** (or **New app**).
3. Pick your repo (`famille-francais`), branch `main`, and for **Main file
   path** type: `app.py`
4. Before clicking deploy, click **"Advanced settings"** and paste this
   into the **Secrets** box (replace with your real key from
   [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)):

   ```
   ANTHROPIC_API_KEY = "sk-ant-your-real-key-here"
   ```

5. Click **Deploy**. Wait a minute or two while it installs everything.
6. You'll land on a page with a URL like `https://famille-francais.streamlit.app`
   -- **this is the link you and your sister will use forever.** Bookmark
   it / text it to her.

---

## Step 4 (recommended) -- Sauvegarde qui survit aux redémarrages (persistent backup)

Streamlit's free hosting occasionally restarts the app (after inactivity,
or when you update the code). Without this step, a restart *could* wipe
your streaks and XP back to zero, because the free tier's storage isn't
permanent. This step fixes that -- takes about 3 minutes, also free.

1. Go to [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta),
   click **Generate new token**.
2. Give it any name, set **Expiration** to whatever you like (e.g. "No
   expiration" or 1 year), and under **Permissions**, find **Gists** and
   set it to **Read and write**. Click **Generate token**, then **copy
   the token** shown (starts with `github_pat_...`) -- you won't be able
   to see it again.
3. Go to [gist.github.com](https://gist.github.com), create a new Gist:
   - Filename: `family_data.json`
   - Content: just type `{}`
   - Click **Create secret gist**.
4. Copy the Gist's ID from its URL -- e.g. if the URL is
   `https://gist.github.com/yourname/abc123def456`, the ID is
   `abc123def456`.
5. Back in your Streamlit app's settings (⋮ menu on your app at
   share.streamlit.io -> **Settings** -> **Secrets**), add two more lines:

   ```
   GITHUB_TOKEN = "github_pat_your-real-token-here"
   GIST_ID = "abc123def456"
   ```

6. Save. The app will restart automatically. Open **⚙️ Réglages** in the
   app -- you should see "Sauvegarde persistante activée (GitHub Gist)".

From now on, progress is saved to that private Gist every time either of
you does anything in the app, so it survives restarts.

---

## Step 5 -- Get it on her iPhone

1. Send her the `https://....streamlit.app` link (text, email, whatever).
2. She opens it in **Safari** (must be Safari, not Chrome, for the next
   step to work on iPhone).
3. Tap the **Share** icon (square with an arrow) -> **Add to Home Screen**.
4. It now sits on her home screen with an icon, opens full-screen like a
   real app -- even though it's just a website under the hood.

She creates her own profile the first time she opens it (or picks her
name from the dropdown if you already created it together).

---

## Updating the app later

If you tweak `core/content_bank.py` (to add vocab, scenarios, etc.) on
your computer, go back to your GitHub repo, open that file, click the
pencil (✏️) icon to edit it directly in the browser, paste the new
version in, and commit. Streamlit Cloud detects the change and
redeploys automatically within a minute or two -- no re-upload of
everything needed.

---

## Costs recap

- GitHub account: free.
- Streamlit Community Cloud hosting: free.
- GitHub Gist storage: free.
- Claude API usage: pay-per-message, typically a few cents for a full day
  of use with the default Haiku model (see README.md for details).

Nothing here requires a credit card except optionally adding funds to
your Anthropic account for API usage.
