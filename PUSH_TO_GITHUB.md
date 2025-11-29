# 🚀 Commands to Push Code to GitHub

## ⚠️ PREREQUISITE: Install Git First

If Git is not installed, download and install from:
**https://git-scm.com/download/win**

After installation, **close and reopen your PowerShell/terminal**.

---

## 📋 STEP-BY-STEP COMMANDS

Copy and paste these commands **one by one** in your PowerShell terminal:

### Step 1: Navigate to Project (if not already there)
```powershell
cd D:\Health_Food_Monitor
```

### Step 2: Initialize Git Repository
```powershell
git init
```

### Step 3: Configure Git (First time only - replace with your info)
```powershell
git config user.name "Chandan"
git config user.email "your.email@example.com"
```

### Step 4: Add All Files
```powershell
git add .
```

### Step 5: Create First Commit
```powershell
git commit -m "Initial commit: Health Food Monitor Flask app ready for deployment"
```

### Step 6: Set Main Branch
```powershell
git branch -M main
```

### Step 7: Add GitHub Remote
```powershell
git remote add origin https://github.com/Chandan-1818/FOOD-NUTRIENTS-MEAL-PLANNER.git
```

### Step 8: Push to GitHub
```powershell
git push -u origin main
```

**Note:** When you run `git push`, you'll be prompted for:
- **Username:** Your GitHub username (Chandan-1818)
- **Password:** Use a **Personal Access Token** (not your GitHub password)

---

## 🔑 How to Get Personal Access Token (for Git Push)

If you get authentication errors:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: "Health Food Monitor Deployment"
4. Select scopes: Check **"repo"** (this gives full repository access)
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)
7. When `git push` asks for password, **paste the token** (not your GitHub password)

---

## ✅ Verification

After successful push, check your GitHub repository:
**https://github.com/Chandan-1818/FOOD-NUTRIENTS-MEAL-PLANNER**

You should see all your files there!

---

## 🎯 Next Step After Push

Once code is on GitHub, we'll proceed to:
- **STEP 3: Deploy to Render**
- Configure environment variables
- Set up database
- Get your public HTTPS URL!

