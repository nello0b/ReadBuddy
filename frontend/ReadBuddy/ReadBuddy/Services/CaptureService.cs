// ReadBuddy\Services\CaptureService.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media.Imaging;
using Microsoft.Extensions.DependencyInjection;

namespace ReadBuddy.Services
{
    public class CaptureService : IDisposable
    {
        private readonly IDialogService _dialogService;
        private EventHandler<string>? _imageCaptured;

        public CaptureService(IDialogService dialogService)
        {
            _dialogService = dialogService;
        }

        public CaptureService() : this(App.ServiceProvider.GetRequiredService<IDialogService>())
        {
        }

        /// <summary>
        /// Subscribes a single handler to the ImageCaptured event.
        /// If a handler is already registered and the event has not fired,
        /// subsequent calls are ignored until the event is invoked.
        /// </summary>
        public void SubscribeImageCaptured(EventHandler<string> handler)
        {
            if (_imageCaptured != null)
                return;

            _imageCaptured = handler;
        }

        private bool _isListening;
        private IntPtr _hwnd;
        private HwndSource? _hwndSource;

        public void StartCapture(Window window)
        {
            if (_isListening)
                return;

            _isListening = true;
            _hwnd = new WindowInteropHelper(window).Handle;
            _hwndSource = HwndSource.FromHwnd(_hwnd);
            _hwndSource.AddHook(WndProc);
            AddClipboardFormatListener(_hwnd);

            Process.Start(new ProcessStartInfo
            {
                FileName = "ms-screenclip:",
                UseShellExecute = true
            });
        }

        /// <summary>
        /// Stops listening for clipboard updates without saving an image. This
        /// can be used if the capture operation is cancelled.
        /// </summary>
        public void StopCapture()
        {
            if (_isListening)
            {
                RemoveClipboardFormatListener(_hwnd);
                _hwndSource?.RemoveHook(WndProc);
            }

            _isListening = false;
            _imageCaptured = null;
        }

        private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            const int WM_CLIPBOARDUPDATE = 0x031D;

            if (_isListening && msg == WM_CLIPBOARDUPDATE)
            {
                _isListening = false;
                RemoveClipboardFormatListener(_hwnd);
                _hwndSource?.RemoveHook(WndProc);

                var image = TryGetClipboardImage();
                if (image != null)
                    SaveImage(image);
            }

            return IntPtr.Zero;
        }

        private static BitmapSource? TryGetClipboardImage()
        {
            const int retries = 5;
            const int delayMs = 50;

            for (int i = 0; i < retries; i++)
            {
                try
                {
                    if (Clipboard.ContainsImage())
                        return Clipboard.GetImage();
                }
                catch (COMException)
                {
                    Thread.Sleep(delayMs);
                }
            }

            return null;
        }

        private void SaveImage(BitmapSource image)
        {
            try
            {
                string path = Path.Combine(Path.GetTempPath(), $"ReadBuddy_Snip_{Guid.NewGuid()}.png");

                using (var fileStream = new FileStream(path, FileMode.Create))
                {
                    PngBitmapEncoder encoder = new();
                    encoder.Frames.Add(BitmapFrame.Create(image));
                    encoder.Save(fileStream);
                }

                _imageCaptured?.Invoke(this, path);
                _imageCaptured = null;
            }
            catch (Exception ex)
            {
                _dialogService.ShowError("Error saving snip: " + ex.Message);
            }
        }

        public void Dispose()
        {
            StopCapture();
        }

        [DllImport("user32.dll")]
        private static extern bool AddClipboardFormatListener(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern bool RemoveClipboardFormatListener(IntPtr hwnd);
    }
}
