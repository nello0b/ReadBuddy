# 🔧 ReadBuddy Frontend Services

The Services layer provides the business logic and external API integration for the ReadBuddy WPF application. This layer abstracts complex operations, manages external dependencies, and provides a clean interface between the ViewModels and external systems.

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │    Core     │ │    Data     │ │    External         │ │
│  │  Services   │ │  Services   │ │   Services          │ │
│  │             │ │             │ │                     │ │
│  │ • Dialog    │ │ • History   │ │ • Backend API       │ │
│  │ • Capture   │ │ • Repository│ │ • Auth0             │ │
│  │ • Session   │ │ • Manager   │ │ • OCR               │ │
│  │ • Tracking  │ │ • Processor │ │ • Task Tracking     │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                Interface Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ IAuthService│ │ IDialog     │ │ IUserSession        │ │
│  │             │ │ Service     │ │ Service             │ │
│  │ • Login     │ │             │ │                     │ │
│  │ • Logout    │ │ • Show      │ │ • GetUser           │ │
│  │ • Refresh   │ │ • Confirm   │ │ • SaveSettings      │ │
│  │ • Validate  │ │ • Error     │ │ • LoadSettings      │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📁 Service Structure

### 🔐 Authentication Services

- **`Auth0Service.cs`**: Auth0 integration and authentication management
- **`IAuthService.cs`**: Authentication service interface
- **`UserSessionService.cs`**: User session and profile management
- **`IUserSessionService.cs`**: User session service interface

### 🌐 Backend Communication

- **`BackendService.cs`**: REST API communication with backend server
- **`TaskTrackerService.cs`**: Background task monitoring and status tracking
- **`TaskTrackingHistoryService.cs`**: Task history and progress tracking

### 🖼️ Screen Capture & Processing

- **`CaptureService.cs`**: Screen capture and screenshot functionality
- **`DocumentProcessor.cs`**: Document processing and text extraction
- **`OcrDeserializer.cs`**: OCR result deserialization and parsing
- **`IOcrDeserializer.cs`**: OCR deserializer interface

### 📚 Content Management

- **`QuizManager.cs`**: Quiz creation and management
- **`GlossaryManager.cs`**: Glossary creation and management
- **`SummaryRepository.cs`**: Summary storage and retrieval
- **`ExtractionRepository.cs`**: Text extraction data management

### 📊 History & Data Services

- **`ExtractionHistoryService.cs`**: OCR extraction history management
- **`QuizHistoryService.cs`**: Quiz history and progress tracking
- **`GlossaryHistoryService.cs`**: Glossary history and bookmarks

### 🎨 UI & Dialog Services

- **`DialogService.cs`**: Dialog and modal window management
- **`IDialogService.cs`**: Dialog service interface

### 🔧 Utility Services

- **`GeometryHelper.cs`**: Geometry calculations and screen measurements
- **`VisualTreeHelperExtensions.cs`**: WPF visual tree manipulation utilities

## 🔐 Authentication Services

### Auth0Service

Handles all authentication operations using Auth0 OIDC client.

```csharp
public class Auth0Service : IAuthService
{
    private readonly Auth0Client _auth0Client;
    private readonly ILogger<Auth0Service> _logger;

    public async Task<LoginResult> LoginAsync()
    {
        try
        {
            var loginResult = await _auth0Client.LoginAsync();

            if (loginResult.IsError)
            {
                _logger.LogError("Login failed: {Error}", loginResult.Error);
                return new LoginResult { IsError = true, Error = loginResult.Error };
            }

            // Store user information
            await StoreUserInfoAsync(loginResult.User);

            return loginResult;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception during login");
            return new LoginResult { IsError = true, Error = ex.Message };
        }
    }

    public async Task<LogoutResult> LogoutAsync()
    {
        try
        {
            await _auth0Client.LogoutAsync();
            await ClearUserInfoAsync();

            return new LogoutResult { IsSuccess = true };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception during logout");
            return new LogoutResult { IsSuccess = false, Error = ex.Message };
        }
    }
}
```

### UserSessionService

Manages user session state and preferences.

```csharp
public class UserSessionService : IUserSessionService
{
    private User _currentUser;
    private readonly ILocalStorageService _localStorage;

    public User CurrentUser => _currentUser;
    public bool IsAuthenticated => _currentUser != null;

    public async Task<User> GetUserAsync()
    {
        if (_currentUser == null)
        {
            _currentUser = await _localStorage.GetItemAsync<User>("current_user");
        }
        return _currentUser;
    }

    public async Task SaveUserAsync(User user)
    {
        _currentUser = user;
        await _localStorage.SetItemAsync("current_user", user);
    }

    public async Task ClearUserAsync()
    {
        _currentUser = null;
        await _localStorage.RemoveItemAsync("current_user");
    }
}
```

## 🌐 Backend Communication

### BackendService

Central service for all backend API communications.

```csharp
public class BackendService
{
    private readonly HttpClient _httpClient;
    private readonly IAuthService _authService;
    private readonly ILogger<BackendService> _logger;

    public async Task<ApiResponse<T>> PostAsync<T>(string endpoint, object data)
    {
        try
        {
            var token = await _authService.GetTokenAsync();
            _httpClient.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", token);

            var json = JsonSerializer.Serialize(data);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync(endpoint, content);

            if (response.IsSuccessStatusCode)
            {
                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<T>(responseContent);
                return new ApiResponse<T> { IsSuccess = true, Data = result };
            }
            else
            {
                _logger.LogError("API call failed: {StatusCode} - {ReasonPhrase}",
                    response.StatusCode, response.ReasonPhrase);
                return new ApiResponse<T> { IsSuccess = false, Error = response.ReasonPhrase };
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception during API call to {Endpoint}", endpoint);
            return new ApiResponse<T> { IsSuccess = false, Error = ex.Message };
        }
    }
}
```

### TaskTrackerService

Monitors background tasks and provides real-time status updates.

```csharp
public class TaskTrackerService
{
    private readonly BackendService _backendService;
    private readonly Dictionary<string, TaskStatus> _trackedTasks;
    private readonly Timer _pollingTimer;

    public event EventHandler<TaskStatusUpdatedEventArgs> TaskStatusUpdated;

    public async Task<string> StartTaskAsync(string taskType, object taskData)
    {
        var response = await _backendService.PostAsync<TaskResponse>(
            $"/tasks/{taskType}", taskData);

        if (response.IsSuccess)
        {
            var taskId = response.Data.TaskId;
            _trackedTasks[taskId] = new TaskStatus
            {
                Id = taskId,
                Type = taskType,
                Status = "pending",
                StartTime = DateTime.UtcNow
            };

            return taskId;
        }

        throw new Exception($"Failed to start task: {response.Error}");
    }

    private async Task PollTaskStatusAsync()
    {
        var taskIds = _trackedTasks.Keys.ToList();

        foreach (var taskId in taskIds)
        {
            var response = await _backendService.GetAsync<TaskStatus>($"/tasks/{taskId}");

            if (response.IsSuccess)
            {
                var updatedStatus = response.Data;
                _trackedTasks[taskId] = updatedStatus;

                TaskStatusUpdated?.Invoke(this, new TaskStatusUpdatedEventArgs
                {
                    TaskId = taskId,
                    Status = updatedStatus
                });

                if (updatedStatus.Status == "completed" || updatedStatus.Status == "failed")
                {
                    _trackedTasks.Remove(taskId);
                }
            }
        }
    }
}
```

## 🖼️ Screen Capture Services

### CaptureService

Handles screen capture functionality with advanced features.

```csharp
public class CaptureService
{
    private readonly ILogger<CaptureService> _logger;
    private bool _isCapturing;

    public async Task<CaptureResult> CaptureScreenAreaAsync()
    {
        try
        {
            _isCapturing = true;

            // Hide the main window during capture
            var mainWindow = Application.Current.MainWindow;
            mainWindow.WindowState = WindowState.Minimized;

            // Wait for window to minimize
            await Task.Delay(200);

            // Create capture overlay
            var captureOverlay = new CaptureOverlay();
            captureOverlay.ShowDialog();

            if (captureOverlay.CaptureResult != null)
            {
                var bitmap = captureOverlay.CaptureResult;
                var imageBytes = BitmapToBytes(bitmap);

                return new CaptureResult
                {
                    IsSuccess = true,
                    ImageData = imageBytes,
                    CaptureArea = captureOverlay.SelectedArea,
                    Timestamp = DateTime.UtcNow
                };
            }

            return new CaptureResult { IsSuccess = false, Error = "Capture cancelled" };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception during screen capture");
            return new CaptureResult { IsSuccess = false, Error = ex.Message };
        }
        finally
        {
            _isCapturing = false;
            // Restore main window
            Application.Current.MainWindow.WindowState = WindowState.Normal;
        }
    }

    private byte[] BitmapToBytes(BitmapSource bitmap)
    {
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));

        using var stream = new MemoryStream();
        encoder.Save(stream);
        return stream.ToArray();
    }
}
```

### DocumentProcessor

Processes captured documents and extracts text.

```csharp
public class DocumentProcessor
{
    private readonly BackendService _backendService;
    private readonly IOcrDeserializer _ocrDeserializer;

    public async Task<DocumentProcessingResult> ProcessDocumentAsync(byte[] imageData)
    {
        try
        {
            // Upload image for OCR processing
            var uploadResult = await _backendService.UploadImageAsync(imageData);

            if (!uploadResult.IsSuccess)
            {
                return new DocumentProcessingResult
                {
                    IsSuccess = false,
                    Error = uploadResult.Error
                };
            }

            // Wait for OCR processing to complete
            var ocrResult = await WaitForOcrCompletionAsync(uploadResult.Data.TaskId);

            if (ocrResult.IsSuccess)
            {
                var extractedText = _ocrDeserializer.DeserializeOcrResult(ocrResult.Data);

                return new DocumentProcessingResult
                {
                    IsSuccess = true,
                    ExtractedText = extractedText,
                    Confidence = ocrResult.Data.Confidence,
                    ProcessingTime = ocrResult.Data.ProcessingTime
                };
            }

            return new DocumentProcessingResult
            {
                IsSuccess = false,
                Error = ocrResult.Error
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception during document processing");
            return new DocumentProcessingResult { IsSuccess = false, Error = ex.Message };
        }
    }
}
```

## 📚 Content Management Services

### QuizManager

Manages quiz creation, storage, and retrieval.

```csharp
public class QuizManager
{
    private readonly BackendService _backendService;
    private readonly QuizHistoryService _historyService;

    public async Task<QuizCreationResult> CreateQuizAsync(string text, int questionCount = 5)
    {
        try
        {
            var request = new QuizCreationRequest
            {
                Text = text,
                QuestionCount = questionCount,
                Difficulty = "medium"
            };

            var response = await _backendService.PostAsync<QuizCreationResponse>(
                "/quizzes/create", request);

            if (response.IsSuccess)
            {
                var quiz = response.Data.Quiz;

                // Save to history
                await _historyService.SaveQuizAsync(quiz);

                return new QuizCreationResult
                {
                    IsSuccess = true,
                    Quiz = quiz,
                    TaskId = response.Data.TaskId
                };
            }

            return new QuizCreationResult { IsSuccess = false, Error = response.Error };
        }
        catch (Exception ex)
        {
            return new QuizCreationResult { IsSuccess = false, Error = ex.Message };
        }
    }

    public async Task<QuizResult> SubmitQuizAnswersAsync(string quizId, Dictionary<int, string> answers)
    {
        try
        {
            var request = new QuizSubmissionRequest
            {
                QuizId = quizId,
                Answers = answers,
                SubmissionTime = DateTime.UtcNow
            };

            var response = await _backendService.PostAsync<QuizResult>(
                $"/quizzes/{quizId}/submit", request);

            if (response.IsSuccess)
            {
                // Update history with results
                await _historyService.UpdateQuizResultAsync(quizId, response.Data);

                return response.Data;
            }

            throw new Exception($"Failed to submit quiz: {response.Error}");
        }
        catch (Exception ex)
        {
            throw new Exception($"Exception during quiz submission: {ex.Message}");
        }
    }
}
```

### GlossaryManager

Manages glossary creation and term definitions.

```csharp
public class GlossaryManager
{
    private readonly BackendService _backendService;
    private readonly GlossaryHistoryService _historyService;

    public async Task<GlossaryCreationResult> CreateGlossaryAsync(string text)
    {
        try
        {
            var request = new GlossaryCreationRequest
            {
                Text = text,
                MaxTerms = 20,
                IncludeDefinitions = true
            };

            var response = await _backendService.PostAsync<GlossaryCreationResponse>(
                "/glossary/create", request);

            if (response.IsSuccess)
            {
                var glossary = response.Data.Glossary;

                // Save to history
                await _historyService.SaveGlossaryAsync(glossary);

                return new GlossaryCreationResult
                {
                    IsSuccess = true,
                    Glossary = glossary,
                    TaskId = response.Data.TaskId
                };
            }

            return new GlossaryCreationResult { IsSuccess = false, Error = response.Error };
        }
        catch (Exception ex)
        {
            return new GlossaryCreationResult { IsSuccess = false, Error = ex.Message };
        }
    }

    public async Task<TermDefinition> GetTermDefinitionAsync(string term)
    {
        try
        {
            var response = await _backendService.GetAsync<TermDefinition>(
                $"/glossary/definition/{Uri.EscapeDataString(term)}");

            if (response.IsSuccess)
            {
                return response.Data;
            }

            throw new Exception($"Failed to get term definition: {response.Error}");
        }
        catch (Exception ex)
        {
            throw new Exception($"Exception getting term definition: {ex.Message}");
        }
    }
}
```

## 📊 History Services

### ExtractionHistoryService

Manages the history of text extractions and OCR results.

```csharp
public class ExtractionHistoryService
{
    private readonly ILocalStorageService _localStorage;
    private readonly BackendService _backendService;
    private const string HISTORY_KEY = "extraction_history";

    public async Task<List<ExtractionHistoryItem>> GetHistoryAsync()
    {
        try
        {
            // Try to get from local storage first
            var localHistory = await _localStorage.GetItemAsync<List<ExtractionHistoryItem>>(HISTORY_KEY);

            if (localHistory != null && localHistory.Any())
            {
                return localHistory;
            }

            // Fallback to backend
            var response = await _backendService.GetAsync<List<ExtractionHistoryItem>>("/history/extractions");

            if (response.IsSuccess)
            {
                await _localStorage.SetItemAsync(HISTORY_KEY, response.Data);
                return response.Data;
            }

            return new List<ExtractionHistoryItem>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception getting extraction history");
            return new List<ExtractionHistoryItem>();
        }
    }

    public async Task SaveExtractionAsync(ExtractionHistoryItem item)
    {
        try
        {
            var history = await GetHistoryAsync();
            history.Insert(0, item); // Add to beginning

            // Keep only last 100 items
            if (history.Count > 100)
            {
                history = history.Take(100).ToList();
            }

            await _localStorage.SetItemAsync(HISTORY_KEY, history);

            // Also save to backend
            await _backendService.PostAsync<object>("/history/extractions", item);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Exception saving extraction history");
        }
    }
}
```

## 🎨 UI Services

### DialogService

Manages dialog windows and user interactions.

```csharp
public class DialogService : IDialogService
{
    public async Task<MessageBoxResult> ShowMessageAsync(string title, string message, MessageBoxButton buttons = MessageBoxButton.OK)
    {
        var dialog = new ModernMessageBox
        {
            Title = title,
            Message = message,
            Buttons = buttons,
            Owner = Application.Current.MainWindow
        };

        return await dialog.ShowAsync();
    }

    public async Task<bool> ShowConfirmationAsync(string title, string message)
    {
        var result = await ShowMessageAsync(title, message, MessageBoxButton.YesNo);
        return result == MessageBoxResult.Yes;
    }

    public async Task<string> ShowInputDialogAsync(string title, string prompt, string defaultValue = "")
    {
        var dialog = new InputDialog
        {
            Title = title,
            Prompt = prompt,
            InputText = defaultValue,
            Owner = Application.Current.MainWindow
        };

        var result = await dialog.ShowAsync();
        return result.IsConfirmed ? result.InputText : null;
    }

    public async Task<string> ShowFileDialogAsync(string filter = "All Files (*.*)|*.*")
    {
        var dialog = new OpenFileDialog
        {
            Filter = filter,
            CheckFileExists = true,
            CheckPathExists = true
        };

        return dialog.ShowDialog() == true ? dialog.FileName : null;
    }
}
```

## 🔧 Utility Services

### GeometryHelper

Provides geometry calculations for screen capture and UI positioning.

```csharp
public static class GeometryHelper
{
    public static Rect GetScreenBounds()
    {
        var left = SystemParameters.VirtualScreenLeft;
        var top = SystemParameters.VirtualScreenTop;
        var width = SystemParameters.VirtualScreenWidth;
        var height = SystemParameters.VirtualScreenHeight;

        return new Rect(left, top, width, height);
    }

    public static Point GetCenterPoint(Rect rect)
    {
        return new Point(rect.X + rect.Width / 2, rect.Y + rect.Height / 2);
    }

    public static Rect NormalizeRect(Point startPoint, Point endPoint)
    {
        var left = Math.Min(startPoint.X, endPoint.X);
        var top = Math.Min(startPoint.Y, endPoint.Y);
        var right = Math.Max(startPoint.X, endPoint.X);
        var bottom = Math.Max(startPoint.Y, endPoint.Y);

        return new Rect(left, top, right - left, bottom - top);
    }

    public static bool IsPointInRect(Point point, Rect rect)
    {
        return point.X >= rect.X && point.X <= rect.Right &&
               point.Y >= rect.Y && point.Y <= rect.Bottom;
    }
}
```

## 🧪 Testing Services

### Service Testing Strategy

Services are tested using:

- **Unit Tests**: Individual service method testing
- **Integration Tests**: Service interaction testing
- **Mock Services**: External dependency mocking
- **Performance Tests**: Service performance validation

### Example Service Test

```csharp
[TestClass]
public class BackendServiceTests
{
    private BackendService _backendService;
    private Mock<IAuthService> _mockAuthService;
    private Mock<HttpClient> _mockHttpClient;

    [TestInitialize]
    public void Setup()
    {
        _mockAuthService = new Mock<IAuthService>();
        _mockHttpClient = new Mock<HttpClient>();
        _backendService = new BackendService(_mockHttpClient.Object, _mockAuthService.Object);
    }

    [TestMethod]
    public async Task PostAsync_ShouldReturnSuccess_WhenApiCallSucceeds()
    {
        // Arrange
        var testData = new { message = "test" };
        var expectedResponse = new { result = "success" };

        _mockAuthService.Setup(x => x.GetTokenAsync())
            .ReturnsAsync("test-token");

        // Act
        var result = await _backendService.PostAsync<object>("/test", testData);

        // Assert
        Assert.IsTrue(result.IsSuccess);
        Assert.IsNotNull(result.Data);
    }
}
```

## 🚀 Performance Optimization

### Service Performance

- **Caching**: Implement intelligent caching strategies
- **Async Operations**: Use async/await for all I/O operations
- **Connection Pooling**: Reuse HTTP connections
- **Resource Management**: Proper disposal of resources
- **Memory Management**: Minimize memory allocations

### Best Practices

- **Dependency Injection**: Use DI for service management
- **Interface Segregation**: Keep interfaces focused and small
- **Error Handling**: Comprehensive error handling with logging
- **Configuration**: Externalize configuration settings
- **Testability**: Design services for easy testing

---

**The Services layer is the backbone of the ReadBuddy frontend application, providing robust, scalable, and maintainable business logic that powers the user experience.**
