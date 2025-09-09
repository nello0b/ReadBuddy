// ReadBuddy\App.xaml.cs
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Net.Http;
using System.Windows;
using Microsoft.Extensions.Http;
using ReadBuddy.Services;
using ReadBuddy.ViewModels;
using ReadBuddy.Views;
using ReadBuddy.Views.Controls;
using ReadBuddy.Views.Flashcards;
using Mvvm.Navigation;
using ReadBuddy.Services.Interfaces;
using ReadBuddy.Views.Home;
using ReadBuddy.ViewModels.Home;
using ReadBuddy.Models.TTS;

namespace ReadBuddy
{
    public partial class App : Application
    {
        public static IServiceProvider ServiceProvider { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var services = new ServiceCollection();

            // ✅ Register HttpClient support
            services.AddHttpClient<BackendService>();
            services.AddSingleton<DocumentProcessor>();
            services.AddSingleton<TaskTrackerService>();
            services.AddTransient<ExtractionRepository>();
            services.AddTransient<SummaryRepository>();
            services.AddSingleton<ExtractionHistoryService>();
            services.AddSingleton<QuizManager>();
            services.AddSingleton<QuizHistoryService>(sp =>
                new QuizHistoryService(sp.GetRequiredService<QuizManager>(),
                                        sp.GetRequiredService<ExtractionRepository>(),
                                        sp.GetRequiredService<IDialogService>()));
            services.AddSingleton<GlossaryManager>();
            services.AddSingleton<GlossaryHistoryService>(sp =>
                new GlossaryHistoryService(sp.GetRequiredService<GlossaryManager>(),
                                          sp.GetRequiredService<ExtractionRepository>(),
                                          sp.GetRequiredService<IDialogService>()));

            // ✅ Register Auth services
            services.AddSingleton<IAuthService, Auth0Service>();
            services.AddSingleton<IUserSessionService, UserSessionService>();
            services.AddSingleton<IOcrDeserializer, OcrDeserializer>();
            services.AddSingleton<IDialogService, DialogService>();

            // ✅ Register ViewModels
            services.AddSingleton<MainViewModel>();
            services.AddSingleton<WelcomeViewModel>();
            services.AddSingleton<QuizHubViewModel>();
            services.AddSingleton<FlashcardHubViewModel>();
            services.AddTransient<HistoryListViewModel>();
            services.AddTransient<HistoryViewModel>();

            // Use a single HomeViewModel instance so History and Home share state
            services.AddSingleton<HomeViewModel>();
            services.AddTransient<OcrHomeViewModel>();
            services.AddTransient<HomeHubViewModel>();

            // ✅ Register Views
            services.AddTransient<MainWindow>();
            services.AddTransient<WelcomeView>();
            services.AddTransient<OcrImageControl>();
            services.AddTransient<QuizHubView>();
            services.AddTransient<FlashcardHubView>();
            services.AddTransient<HistoryListView>();
            services.AddTransient<HistoryView>();

            services.AddTransient<HomeHubView>();
            services.AddTransient<HomeView>();
            services.AddTransient<OcrHomeView>();




            // ✅ Build and assign service provider
            ServiceProvider = services.BuildServiceProvider();

            // 🪟 Show WelcomeView
            var welcomeWindow = ServiceProvider.GetRequiredService<WelcomeView>();
            welcomeWindow.Show();
        }

        protected override void OnExit(ExitEventArgs e)
        {
            try
            {
                // Clear all cached audio files on application shutdown
                TTSResult.ClearAllCachedAudio();
                System.Diagnostics.Debug.WriteLine("🧹 Cleared audio cache on app shutdown");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"❌ Error clearing audio cache on shutdown: {ex.Message}");
            }

            base.OnExit(e);
        }
    }
}
