# How to Create Release v1.0.1

Since Git is not available in this environment, you'll need to create the release from GitHub. Here are the exact steps:

## Method 1: Manual Workflow Trigger (Recommended)

1. Go to your GitHub repository
2. Click on the **Actions** tab
3. Find the **"Build and Release"** workflow in the left sidebar
4. Click on **"Build and Release"**
5. Click the **"Run workflow"** button (top right)
6. In the dropdown:
   - Leave branch as `main` (or your default branch)
   - Enter `1.0.1` in the version field (without 'v' prefix)
7. Click **"Run workflow"**

The workflow will automatically:
- Build executables for Windows, macOS, and Linux
- Generate SHA256 checksums
- Create source archives
- Publish everything as a GitHub release

## Method 2: Create Release Directly

1. Go to your GitHub repository
2. Click **"Releases"** in the right sidebar
3. Click **"Create a new release"**
4. Set tag version: `v1.0.1`
5. Set release title: `Meet-Zone v1.0.1`
6. Copy the content from `RELEASE_NOTES.md` into the description
7. Check **"Set as the latest release"**
8. Click **"Publish release"**

This will trigger the build workflow automatically.

## Method 3: From Local Machine (if you have the code locally)

```bash
# Clone or update your local repository
git clone https://github.com/yourusername/meet-zone.git
cd meet-zone

# Make sure you have the latest changes
git pull origin main

# Create and push the tag
git tag v1.0.1
git push origin v1.0.1
```

## What Happens Next

Once triggered, the GitHub Actions workflow will:

1. **Build Windows executable** (`meet-zone-windows-1.0.1.exe`)
2. **Build macOS executable** (`meet-zone-macos-1.0.1`)
3. **Build Linux executable** (`meet-zone-linux-1.0.1`)
4. **Create source archives** (`.zip` and `.tar.gz`)
5. **Generate SHA256 checksums** for all files
6. **Create GitHub release** with all assets attached

## Expected Release Assets

Your release will include:
- `meet-zone-windows-1.0.1.exe` + checksum
- `meet-zone-macos-1.0.1` + checksum  
- `meet-zone-linux-1.0.1` + checksum
- `meet-zone-source-1.0.1.zip` + checksum
- `meet-zone-source-1.0.1.tar.gz` + checksum

## Troubleshooting

If the workflow fails:
1. Check the Actions tab for error details
2. Ensure all required files are present in the repository
3. Verify the workflow file syntax in `.github/workflows/build.yml`
4. Make sure the repository has the necessary permissions for releases

The build process typically takes 5-10 minutes to complete across all platforms.