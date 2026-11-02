# Publish this portfolio project on GitHub (Windows)

1. Extract the ZIP file and open the `RetailIQ_GitHub_Ready` folder.
2. Install GitHub Desktop from https://desktop.github.com/ and sign in.
3. In GitHub Desktop choose **File → Add local repository → Choose** and select this extracted folder.
4. If GitHub Desktop says this folder is not a Git repository, click **Create a repository here** and confirm.
5. In **Changes**, enter **Initial portfolio release** and click **Commit to main**.
6. Click **Publish repository**, name it `retailiq-ecommerce-analytics-ai`, and uncheck **Keep this code private** when ready to make it public.
7. Open the repository on GitHub and check that the README, tests, and synthetic model files appear.
8. Before approaching clients, add actual screenshots made on your Windows PC: run the app, visit the Overview, Recommendations, and Model Performance pages, capture them with **Win+Shift+S**, and save the PNGs into `reports/`. In GitHub Desktop, commit and push your new screenshots.

**Do not upload** the original Retailrocket CSVs or any outputs trained on those original files into this public repository. This ZIP is intentionally prepared with independent fictional data and a separately trained model.

This is a **GitHub code repository**, not a public hosted dashboard. To provide clients with a live URL, host the FastAPI app separately on a Python-compatible service.
