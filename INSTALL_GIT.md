# Install Git on Windows

## Quick Installation Steps:

### Option 1: Download Git for Windows (Recommended)

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - The download will start automatically
   - File name: `Git-2.x.x-64-bit.exe` (or similar)

2. **Install Git:**
   - Run the downloaded installer
   - Click "Next" through the installation
   - **Important:** On "Adjusting your PATH environment" screen:
     - Select: **"Git from the command line and also from 3rd-party software"**
   - Keep clicking "Next" with default options
   - Click "Install"
   - Wait for installation to complete
   - Click "Finish"

3. **Verify Installation:**
   - Close and reopen your PowerShell/terminal
   - Run: `git --version`
   - You should see: `git version 2.x.x`

### Option 2: Install via Winget (Windows Package Manager)

If you have winget installed:
```powershell
winget install --id Git.Git -e --source winget
```

### Option 3: Install via Chocolatey

If you have Chocolatey installed:
```powershell
choco install git
```

---

## After Installation:

1. **Close and reopen your terminal/PowerShell**
2. **Verify Git works:**
   ```powershell
   git --version
   ```

3. **Configure Git (first time only):**
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

---

## Then Continue Deployment:

Once Git is installed, we'll continue with:
- Initializing the repository
- Adding files
- Committing
- Pushing to GitHub

