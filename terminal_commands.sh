# Initialize git repository (if not already done)
git init

# Add all files to git
git add .

# Commit the changes
git commit -m "Initial commit: HLS Video Streaming Server with React player"

# Add the remote repository
git remote add origin https://github.com/ArunNKutty/VideoStreaming.git

# Push to the repository (you'll need to authenticate)
git push -u origin master
# If the default branch is 'main' instead of 'master', use:
# git push -u origin main