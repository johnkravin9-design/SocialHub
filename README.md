# 🌐 SocialHub - Facebook-like Social Platform

A beautiful, modern social media platform built with Flask, featuring real-time messaging, posts, likes, comments, and more!

## ✨ Features

- 👤 User authentication (Register/Login)
- 📰 News feed with posts
- 📸 Image uploads for posts
- ❤️ Like & Unlike posts
- 💬 Comment on posts
- 🔄 Share functionality
- 👥 Friend system
- 💬 Real-time messaging (WebSocket)
- 📱 Fully responsive design
- 🌙 Beautiful modern UI
- ⚡ Fast and lightweight

## 🚀 Quick Start in Termux

### Installation
```bash
# Install dependencies
pkg update && pkg upgrade -y
pkg install python git sqlite -y

# Clone repository
git clone https://github.com/YOUR_USERNAME/SocialHub.git
cd SocialHub

# Install Python packages
pip install -r requirements.txt
```

### Running the App
```bash
# Start the server
python app.py

# Open in browser
# Navigate to: http://127.0.0.1:5000
```

## 📱 Usage

1. **Register** a new account
2. **Login** with your credentials
3. **Create posts** with text and images
4. **Like and comment** on posts
5. **Send messages** to other users
6. **View profiles** and add friends

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Real-time**: Socket.IO
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login, Werkzeug

## 📂 Project Structure
```
SocialHub/
├── app.py                 # Main application
├── database/
│   ├── models.py         # Database models
│   └── socialhub.db      # SQLite database
├── static/
│   ├── css/style.css     # Styles
│   ├── js/main.js        # JavaScript
│   └── uploads/          # User uploads
├── templates/            # HTML templates
└── requirements.txt      # Dependencies
```

## 🎨 Screenshots

[Add screenshots here after running]

## 🔐 Security Notes

- Change `app.secret_key` in production
- Use HTTPS in production
- Implement rate limiting
- Add CSRF protection
- Sanitize user inputs

## 📝 TODO

- [ ] Add friend requests
- [ ] Implement notifications
- [ ] Add video posts
- [ ] Create groups feature
- [ ] Add stories
- [ ] Implement search
- [ ] Add emoji reactions
- [ ] Create mobile app

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📄 License

MIT License - feel free to use for your projects!

## 👨‍💻 Author

Built with ❤️ using Termux

---

**Made with Flask & Socket.IO** 🚀
