# 🪟 ReadBuddy Frontend - WPF Desktop Application

A modern WPF desktop application that serves as the user interface for ReadBuddy, an AI-powered reading assistant specifically designed to help users with ADHD and dyslexia. The frontend provides an intuitive interface for screen capture, OCR processing, text-to-speech functionality, AI-powered summarization, and interactive learning tools like flashcards and quizzes.

## 🎯 Key Features

### 🖼️ Screen Capture & OCR
- **Smart Screen Capture**: Capture any area of the screen
- **Real-time OCR**: Extract text from images and screenshots
- **Multi-format Support**: JPG, PNG, BMP, TIFF image formats

### 📚 AI-Powered Learning Tools
- **Smart Summarization**: AI-generated summaries of complex text
- **Interactive Quizzes**: Generate quizzes from any text content
- **Glossary Creation**: Automatic glossary generation with definitions
- 
### 🎨 User Experience
- **Material Design**: Modern, clean interface
- **Responsive Layout**: Adaptive UI for different screen sizes

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   WPF Application                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │    Views    │ │ ViewModels  │ │      Models         │ │
│  │             │ │             │ │                     │ │
│  │ • MainView  │ │ • MainVM    │ │ • UserModel         │ │
│  │ • CaptureVM │ │ • CaptureVM │ │ • QuizModel         │ │
│  │ • QuizView  │ │ • QuizVM    │ │ • SummaryModel      │ │
│  │ • HistoryVM │ │ • HistoryVM │ │ • GlossaryModel     │ │
│  │ • SettingsVM│ │ • SettingsVM│ │ • TaskModel         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                Service Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Backend     │ │ Authentication│ │    UI Services     │ │
│  │ Service     │ │   Service    │ │                    │ │
│  │             │ │             │ │ • DialogService     │ │
│  │ • HTTP API  │ │ • Auth0     │ │ • CaptureService    │ │
│  │ • File I/O  │ │ • JWT       │ │ • TaskTracker       │ │
│  │ • Caching   │ │ • Sessions  │ │ • HistoryService    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              External Dependencies                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Backend   │ │   Auth0     │ │   Windows APIs      │ │
│  │     API     │ │             │ │                     │ │
│  │             │ │ • OIDC      │ │ • Screen Capture    │ │
│  │ • FastAPI   │ │ • Profile   │ │ • File System       │ │
│  │ • REST      │ │ • Tokens    │ │ • Clipboard         │ │
│  │ • WebSockets│ │             │ │ • System Tray       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: WPF (.NET 8)
- **Architecture**: MVVM (Model-View-ViewModel)
- **MVVM Toolkit**: CommunityToolkit.Mvvm
- **Authentication**: Auth0 (OIDC Client for WPF)
- **Dependency Injection**: Microsoft.Extensions.DependencyInjection
- **Navigation**: Mvvm.Navigation.Wpf
- **Behaviors**: Microsoft.Xaml.Behaviors.Wpf
- **HTTP Client**: Microsoft.Extensions.Http

## Getting Started

### Prerequisites

- **Visual Studio 2022** (or later) with .NET desktop development workload
- **.NET 8 SDK** or later
- **Windows 10/11** (WPF application)

### Installation & Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/your-org/ReadBuddy.git
   cd ReadBuddy/frontend/ReadBuddy
   ```

2. **Open the solution:**
   ```powershell
   # Open in Visual Studio
   start ReadBuddy.sln
   
   # Or open with VS Code
   code .
   ```

3. **Restore NuGet packages:**
   ```powershell
   dotnet restore
   ```

4. **Build and run:**
   ```powershell
   dotnet build
   dotnet run --project ReadBuddy
   ```

   Or simply press **F5** in Visual Studio to build and run with debugging.

## Configuration Instructions

### Required Configuration

Before running the application, ensure the following settings are configured in `App.config`:

```xml
<appSettings>
    <!-- Auth0 Configuration -->
    <add key="Auth0:Domain" value="your-auth0-domain.auth0.com" />
    <add key="Auth0:ClientId" value="your-auth0-client-id" />
    <add key="Auth0:Audience" value="https://readbuddy/api" />
    <add key="Auth0:RedirectUri" value="http://127.0.0.1:7890" />
    
    <!-- Backend API Configuration -->
    <add key="Backend:BaseUrl" value="http://127.0.0.1:8000" />
</appSettings>
```

### Setup Steps:

1. **Auth0 Setup:**
   - Create an Auth0 application for desktop/native apps
   - Configure the redirect URI to match your local setup
   - Update the `Auth0:Domain` and `Auth0:ClientId` values

2. **Backend Connection:**
   - Ensure the ReadBuddy backend is running locally
   - Update `Backend:BaseUrl` if your backend runs on a different port

## 📁 Project Structure

```
ReadBuddy/
├── 📄 ReadBuddy.sln           # Visual Studio solution file
├── 📄 README.md               # This documentation
└── 📁 ReadBuddy/              # Main WPF project
    ├── 📄 App.xaml            # Application definition
    ├── 📄 App.xaml.cs         # Application code-behind
    ├── 📄 App.config          # Application configuration
    ├── 📄 ReadBuddy.csproj    # Project file
    ├── 📄 AssemblyInfo.cs     # Assembly metadata
    ├── 📁 Views/              # XAML views and user controls
    │   ├── 📄 MainWindow.xaml      # Main application window
    │   ├── 📄 CaptureView.xaml     # Screen capture interface
    │   ├── 📄 QuizView.xaml        # Quiz interface
    │   ├── 📄 SummaryView.xaml     # Summary display
    │   ├── 📄 GlossaryView.xaml    # Glossary interface
    │   ├── 📄 HistoryView.xaml     # History management
    │   ├── 📄 SettingsView.xaml    # Application settings
    │   └── 📄 ...                  # Other views
    ├── 📁 ViewModels/         # MVVM view models
    │   ├── 📄 MainViewModel.cs     # Main window view model
    │   ├── 📄 CaptureViewModel.cs  # Screen capture logic
    │   ├── 📄 QuizViewModel.cs     # Quiz management
    │   ├── 📄 SummaryViewModel.cs  # Summary handling
    │   ├── 📄 GlossaryViewModel.cs # Glossary management
    │   ├── 📄 HistoryViewModel.cs  # History tracking
    │   ├── 📄 SettingsViewModel.cs # Settings management
    │   └── 📄 ...                  # Other view models
    ├── 📁 Models/             # Data models and DTOs
    │   ├── 📄 UserModel.cs         # User data model
    │   ├── 📄 QuizModel.cs         # Quiz data structures
    │   ├── 📄 SummaryModel.cs      # Summary data model
    │   ├── 📄 GlossaryModel.cs     # Glossary data model
    │   ├── 📄 TaskModel.cs         # Task status model
    │   ├── 📄 HistoryModel.cs      # History data model
    │   └── 📄 ...                  # Other models
    ├── 📁 Services/           # Business logic and external APIs
    │   ├── 📄 BackendService.cs         # API communication
    │   ├── 📄 Auth0Service.cs           # Authentication
    │   ├── 📄 CaptureService.cs         # Screen capture logic
    │   ├── 📄 DialogService.cs          # Dialog management
    │   ├── 📄 DocumentProcessor.cs      # Document processing
    │   ├── 📄 TaskTrackerService.cs     # Task monitoring
    │   ├── 📄 ExtractionHistoryService.cs # History management
    │   ├── 📄 QuizManager.cs            # Quiz operations
    │   ├── 📄 GlossaryManager.cs        # Glossary operations
    │   ├── 📄 UserSessionService.cs     # Session management
    │   └── 📄 ...                       # Other services
    ├── 📁 Converters/         # XAML value converters
    │   ├── 📄 BooleanToVisibilityConverter.cs
    │   ├── 📄 InverseBooleanConverter.cs
    │   ├── 📄 StringToVisibilityConverter.cs
    │   └── 📄 ...                       # Other converters
    ├── 📁 Themes/             # Application themes and styles
    │   ├── 📄 Light.xaml               # Light theme
    │   ├── 📄 Dark.xaml                # Dark theme
    │   ├── 📄 MaterialDesign.xaml      # Material design styles
    │   └── 📄 Generic.xaml             # Generic styles
    ├── 📁 Resources/          # Application resources
    │   ├── 📄 Strings.resx             # Localized strings
    │   ├── 📄 Icons.xaml               # Icon resources
    │   └── 📁 Images/                  # Image assets
    ├── 📁 Animations/         # UI animations and transitions
    │   ├── 📄 FadeAnimations.cs        # Fade effects
    │   ├── 📄 SlideAnimations.cs       # Slide transitions
    │   └── 📄 ...                      # Other animations
    ├── 📁 Icon/               # Application icons
    │   ├── 📄 app.ico                  # Main application icon
    │   └── 📄 ...                      # Other icons
    ├── 📁 bin/                # Build output
    └── 📁 obj/                # Build intermediate files
```

## 🔧 Technical Implementation

### MVVM Architecture
- **Models**: Data structures and business objects
- **Views**: XAML user interfaces with minimal code-behind
- **ViewModels**: Presentation logic and data binding
- **Services**: Business logic and external API integration

### Key Technologies
- **.NET 8**: Modern .NET framework
- **WPF**: Windows Presentation Foundation
- **XAML**: Extensible Application Markup Language
- **Material Design**: Modern UI component library
- **Auth0**: Authentication and authorization
- **HttpClient**: REST API communication

### Design Patterns
- **MVVM**: Model-View-ViewModel pattern
- **Dependency Injection**: IoC container for service management
- **Command Pattern**: ICommand implementations for user actions
- **Observer Pattern**: INotifyPropertyChanged for data binding
- **Repository Pattern**: Data access abstraction

## 🔐 Security & Authentication

### Auth0 Integration
- **OpenID Connect**: Industry-standard authentication
- **JWT Tokens**: Secure token-based authentication

### API Communication
- **REST API**: RESTful communication with backend
- **Async/Await**: Non-blocking API calls
- **Error Handling**: Comprehensive error handling and retry logic
- **Offline Support**: Basic offline functionality

## 🔧 Configuration & Settings

### Application Configuration
```xml
<!-- App.config -->
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <appSettings>
    <add key="ApiBaseUrl" value="http://localhost:8000" />
    <add key="Auth0Domain" value="your-domain.auth0.com" />
    <add key="Auth0ClientId" value="your-client-id" />
    <add key="DefaultTheme" value="Light" />
    <add key="EnableLogging" value="true" />
  </appSettings>
</configuration>
```

## 📱 User Workflows

### Screen Capture Workflow
1. **Capture Initiation**: User clicks capture button
2. **Area Selection**: User selects screen area
3. **Image Processing**: Screenshot captured and processed
4. **OCR Processing**: Text extracted from image
5. **Results Display**: Extracted text displayed to user

### Quiz Generation Workflow
1. **Text Input**: User provides text or selects from history
2. **Processing**: Text sent to backend for quiz generation
3. **Task Monitoring**: Real-time progress tracking
4. **Quiz Display**: Generated quiz presented to user
5. **Interaction**: User completes quiz with feedback

## 🔄 State Management

### Application State
- **User Session**: Authentication state and user profile
- **UI State**: Current view, theme, and layout preferences
- **Data State**: Cached data and user-generated content
- **Task State**: Background task progress and status

### Data Binding
- **OneWay**: Data flows from source to target
- **TwoWay**: Bidirectional data binding
- **OneTime**: Single data transfer at initialization
- **OneWayToSource**: Data flows from target to source

## 🚀 Performance Optimization

### UI Performance
- **Virtualization**: UI virtualization for large data sets
- **Data Binding**: Efficient data binding strategies
- **Resource Management**: Proper disposal of resources
- **Memory Management**: Avoiding memory leaks

### API Performance
- **Caching**: Intelligent caching strategies
- **Async Operations**: Non-blocking operations
- **Batch Processing**: Bulk operations when possible
- **Connection Pooling**: Efficient HTTP connection management
