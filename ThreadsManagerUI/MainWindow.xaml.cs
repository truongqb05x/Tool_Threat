using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.Collections.ObjectModel;
using System.Linq;
using ThreadsManagerUI.ViewModels;

namespace ThreadsManagerUI;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainViewModel();
    }

    private void BtnImportAccount_Click(object sender, RoutedEventArgs e)
    {
        var importWindow = new ImportAccountWindow
        {
            Owner = this
        };
        importWindow.ShowDialog();
    }

    private void BtnImportFromFile_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var openFileDialog = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*",
                Title = "Chọn file chứa danh sách tài khoản"
            };

            if (openFileDialog.ShowDialog() == true)
            {
                var fileContent = System.IO.File.ReadAllText(openFileDialog.FileName);
                var importWindow = new ImportAccountWindow
                {
                    Owner = this,
                    InputData = fileContent
                };
                importWindow.ShowDialog();
            }
        }
        catch (System.Exception ex)
        {
            System.Windows.MessageBox.Show("Lỗi khi mở file: " + ex.Message, "Lỗi", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
        }
    }

    private void BtnSettings_Click(object sender, RoutedEventArgs e)
    {
        var settingsWindow = new SettingsWindow
        {
            Owner = this
        };
        settingsWindow.ShowDialog();
    }

    private void DgAccounts_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (TxtSelectedCount != null && DgAccounts != null)
        {
            TxtSelectedCount.Text = $"Đã chọn: {DgAccounts.SelectedItems.Count}";
        }
    }

    private void CboStatusFilter_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
    {
        ApplyFilters();
    }

    private void TxtSearch_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)
    {
        ApplyFilters();
    }

    private void BtnSearch_Click(object sender, RoutedEventArgs e)
    {
        ApplyFilters();
    }

    private void ApplyFilters()
    {
        var mainViewModel = DataContext as MainViewModel;
        if (mainViewModel == null || DgAccounts == null) return;
        
        var selectedItem = CboStatusFilter?.SelectedItem as System.Windows.Controls.ComboBoxItem;
        string statusFilter = selectedItem?.Content.ToString() ?? "All Status";
        string searchText = TxtSearch?.Text.Trim().ToLower() ?? "";

        var view = System.Windows.Data.CollectionViewSource.GetDefaultView(mainViewModel.Accounts);
        view.Filter = item =>
        {
            var acc = item as Models.AccountModel;
            if (acc == null) return false;

            bool matchesStatus = (statusFilter == "All Status") || (acc.Status == statusFilter);
            bool matchesSearch = string.IsNullOrEmpty(searchText) || (!string.IsNullOrEmpty(acc.Uid) && acc.Uid.ToLower().Contains(searchText));

            return matchesStatus && matchesSearch;
        };
    }

    private void MenuItem_Delete_Click(object sender, RoutedEventArgs e)
    {
        var mainViewModel = DataContext as MainViewModel;
        if (mainViewModel == null) return;

        var selectedItems = DgAccounts.SelectedItems.Cast<Models.AccountModel>().ToList();
        if (selectedItems.Count == 0) return;

        var result = System.Windows.MessageBox.Show($"Bạn có chắc chắn muốn xóa {selectedItems.Count} tài khoản đã chọn và cả profile Chrome của chúng (nếu có)?", "Xác nhận xóa", System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Question);
        if (result != System.Windows.MessageBoxResult.Yes) return;

        string pythonScriptDir = System.AppDomain.CurrentDomain.BaseDirectory;
        if (!System.IO.File.Exists(System.IO.Path.Combine(pythonScriptDir, "main.py")))
        {
            pythonScriptDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(pythonScriptDir, @"..\..\..\.."));
        }
        string profilesDir = System.IO.Path.Combine(pythonScriptDir, "profiles");

        foreach (var item in selectedItems)
        {
            if (!string.IsNullOrEmpty(item.Uid))
            {
                string profilePath = System.IO.Path.Combine(profilesDir, item.Uid);
                if (System.IO.Directory.Exists(profilePath))
                {
                    try
                    {
                        System.IO.Directory.Delete(profilePath, true);
                    }
                    catch (System.Exception ex)
                    {
                        System.Windows.MessageBox.Show($"Không thể xóa profile của {item.Uid}: {ex.Message}", "Lỗi", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                    }
                }
            }
            mainViewModel.Accounts.Remove(item);
        }

        // Cập nhật lại cột STT (Index)
        for (int i = 0; i < mainViewModel.Accounts.Count; i++)
        {
            mainViewModel.Accounts[i].Index = i + 1;
        }
    }

    private void MenuItem_OpenChrome_Click(object sender, RoutedEventArgs e)
    {
        var selectedItem = DgAccounts.SelectedItem as Models.AccountModel;
        if (selectedItem == null || string.IsNullOrEmpty(selectedItem.Uid)) return;

        try
        {
            LoadingOverlay.Visibility = System.Windows.Visibility.Visible;
            TxtLoadingStatus.Text = $"Đang mở Chrome cho {selectedItem.Uid}...";

            string pythonScriptDir = System.AppDomain.CurrentDomain.BaseDirectory;
            if (!System.IO.File.Exists(System.IO.Path.Combine(pythonScriptDir, "main.py")))
            {
                pythonScriptDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(pythonScriptDir, @"..\..\..\.."));
            }
            
            var processInfo = new System.Diagnostics.ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"-u main.py open_chrome \"{selectedItem.Uid}\"",
                WorkingDirectory = pythonScriptDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8
            };
            
            var process = new System.Diagnostics.Process();
            process.StartInfo = processInfo;
            process.EnableRaisingEvents = true;

            process.OutputDataReceived += (s, args) =>
            {
                if (args.Data != null)
                {
                    if (args.Data.Contains("[CHROME_READY]") || args.Data.Contains("[CHROME_ERROR]"))
                    {
                        Dispatcher.Invoke(() =>
                        {
                            LoadingOverlay.Visibility = System.Windows.Visibility.Collapsed;
                            if (args.Data.Contains("[CHROME_ERROR]"))
                            {
                                System.Windows.MessageBox.Show("Có lỗi khi mở Chrome. Vui lòng kiểm tra lại cấu hình.", "Lỗi", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
                            }
                        });
                    }
                }
            };
            
            process.Exited += (s, args) =>
            {
                Dispatcher.Invoke(() =>
                {
                    LoadingOverlay.Visibility = System.Windows.Visibility.Collapsed;
                });
            };

            process.Start();
            process.BeginOutputReadLine();
        }
        catch (System.Exception ex)
        {
            LoadingOverlay.Visibility = System.Windows.Visibility.Collapsed;
            System.Windows.MessageBox.Show("Lỗi khi mở Chrome: " + ex.Message, "Lỗi", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
        }
    }

    private void BtnTabKetNoi_Click(object sender, RoutedEventArgs e)
    {
        GridKetNoiThreads.Visibility = Visibility.Visible;
        GridDangBai.Visibility = Visibility.Collapsed;

        GridComment.Visibility = Visibility.Collapsed;
        GridNuoiTaiKhoan.Visibility = Visibility.Collapsed;
        var inactiveBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#666666"));
        
        BtnTabKetNoi.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1877F2"));
        BtnTabKetNoi.Foreground = Brushes.White;
        BtnTabKetNoi.FontWeight = FontWeights.Bold;

        BtnTabDangBai.Background = Brushes.Transparent;
        BtnTabDangBai.Foreground = inactiveBrush;
        BtnTabDangBai.FontWeight = FontWeights.SemiBold;





        BtnTabComment.Background = Brushes.Transparent;
        BtnTabComment.Foreground = inactiveBrush;
        BtnTabComment.FontWeight = FontWeights.SemiBold;
        
        BtnTabNuoiTaiKhoan.Background = Brushes.Transparent;
        BtnTabNuoiTaiKhoan.Foreground = inactiveBrush;
        BtnTabNuoiTaiKhoan.FontWeight = FontWeights.SemiBold;
    }

    private void BtnTabDangBai_Click(object sender, RoutedEventArgs e)
    {
        GridKetNoiThreads.Visibility = Visibility.Collapsed;
        GridDangBai.Visibility = Visibility.Visible;

        GridComment.Visibility = Visibility.Collapsed;
        GridNuoiTaiKhoan.Visibility = Visibility.Collapsed;

        var inactiveBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#666666"));

        BtnTabDangBai.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1877F2"));
        BtnTabDangBai.Foreground = Brushes.White;
        BtnTabDangBai.FontWeight = FontWeights.Bold;

        BtnTabKetNoi.Background = Brushes.Transparent;
        BtnTabKetNoi.Foreground = inactiveBrush;
        BtnTabKetNoi.FontWeight = FontWeights.SemiBold;





        BtnTabComment.Background = Brushes.Transparent;
        BtnTabComment.Foreground = inactiveBrush;
        BtnTabComment.FontWeight = FontWeights.SemiBold;

        BtnTabNuoiTaiKhoan.Background = Brushes.Transparent;
        BtnTabNuoiTaiKhoan.Foreground = inactiveBrush;
        BtnTabNuoiTaiKhoan.FontWeight = FontWeights.SemiBold;
    }


    private void BtnTabComment_Click(object sender, RoutedEventArgs e)
    {
        GridKetNoiThreads.Visibility = Visibility.Collapsed;
        GridDangBai.Visibility = Visibility.Collapsed;

        GridComment.Visibility = Visibility.Visible;
        GridNuoiTaiKhoan.Visibility = Visibility.Collapsed;

        var inactiveBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#666666"));

        BtnTabComment.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1877F2"));
        BtnTabComment.Foreground = Brushes.White;
        BtnTabComment.FontWeight = FontWeights.Bold;

        BtnTabKetNoi.Background = Brushes.Transparent;
        BtnTabKetNoi.Foreground = inactiveBrush;
        BtnTabKetNoi.FontWeight = FontWeights.SemiBold;

        BtnTabDangBai.Background = Brushes.Transparent;
        BtnTabDangBai.Foreground = inactiveBrush;
        BtnTabDangBai.FontWeight = FontWeights.SemiBold;
        




        BtnTabNuoiTaiKhoan.Background = Brushes.Transparent;
        BtnTabNuoiTaiKhoan.Foreground = inactiveBrush;
        BtnTabNuoiTaiKhoan.FontWeight = FontWeights.SemiBold;
    }

    private void BtnTabNuoiTaiKhoan_Click(object sender, RoutedEventArgs e)
    {
        GridKetNoiThreads.Visibility = Visibility.Collapsed;
        GridDangBai.Visibility = Visibility.Collapsed;

        GridComment.Visibility = Visibility.Collapsed;
        GridNuoiTaiKhoan.Visibility = Visibility.Visible;

        var inactiveBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#666666"));

        BtnTabNuoiTaiKhoan.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1877F2"));
        BtnTabNuoiTaiKhoan.Foreground = Brushes.White;
        BtnTabNuoiTaiKhoan.FontWeight = FontWeights.Bold;

        BtnTabKetNoi.Background = Brushes.Transparent;
        BtnTabKetNoi.Foreground = inactiveBrush;
        BtnTabKetNoi.FontWeight = FontWeights.SemiBold;

        BtnTabDangBai.Background = Brushes.Transparent;
        BtnTabDangBai.Foreground = inactiveBrush;
        BtnTabDangBai.FontWeight = FontWeights.SemiBold;
        



        
        BtnTabComment.Background = Brushes.Transparent;
        BtnTabComment.Foreground = inactiveBrush;
        BtnTabComment.FontWeight = FontWeights.SemiBold;
    }

    private void RbSourceExcel_Checked(object sender, RoutedEventArgs e)
    {
        if (PanelExcel != null && PanelGemini != null)
        {
            PanelExcel.Visibility = Visibility.Visible;
            PanelGemini.Visibility = Visibility.Collapsed;
        }
    }

    private void RbSourceGemini_Checked(object sender, RoutedEventArgs e)
    {
        if (PanelExcel != null && PanelGemini != null)
        {
            PanelExcel.Visibility = Visibility.Collapsed;
            PanelGemini.Visibility = Visibility.Visible;
        }
    }



    private void BtnSelectExcel_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            Title = "Chọn file Excel",
            Filter = "Excel Files|*.xls;*.xlsx;*.xlsm;*.csv|All Files|*.*"
        };

        if (dialog.ShowDialog() == true)
        {
            TxtExcelPath.Text = dialog.FileName;
        }
    }



    private void BtnSelectAccountsForPost_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null) return;
        
        var selectWindow = new SelectAccountWindow(vm.Accounts);
        selectWindow.Owner = this;
        if (selectWindow.ShowDialog() == true)
        {
            var selected = selectWindow.SelectedAccounts;
            foreach (var acc in selected)
            {
                if (!vm.SelectedAccountsForPost.Any(a => a.Uid == acc.Uid))
                {
                    vm.SelectedAccountsForPost.Add(acc);
                }
            }
            
            // Cập nhật lại số thứ tự
            for (int i = 0; i < vm.SelectedAccountsForPost.Count; i++)
            {
                vm.SelectedAccountsForPost[i].Index = i + 1;
            }
        }
    }

    private void BtnRemovePostAccount_Click(object sender, RoutedEventArgs e)
    {
        var button = sender as Button;
        if (button != null)
        {
            var item = button.DataContext as Models.AccountModel;
            if (item != null)
            {
                var vm = this.DataContext as MainViewModel;
                if (vm != null)
                {
                    vm.SelectedAccountsForPost.Remove(item);
                    for (int i = 0; i < vm.SelectedAccountsForPost.Count; i++)
                    {
                        vm.SelectedAccountsForPost[i].Index = i + 1;
                    }
                }
            }
        }
    }

    private void BtnSelectMedia_Click(object sender, RoutedEventArgs e)
    {
        // Simple folder browser dialog simulation using WinForms or OpenFileDialog
        var dialog = new Microsoft.Win32.OpenFileDialog();
        dialog.Title = "Chọn file hình ảnh/video";
        dialog.Multiselect = true;
        dialog.Filter = "Image/Video Files|*.jpg;*.jpeg;*.png;*.mp4|All files (*.*)|*.*";
        if (dialog.ShowDialog() == true)
        {
            TxtMediaPath.Text = string.Join("\n", dialog.FileNames);
        }
    }

    private void BtnSelectCommentExcel_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog();
        dialog.Title = "Chọn file Excel/Text chứa nội dung comment";
        dialog.Filter = "Excel/Text Files|*.xlsx;*.xls;*.txt|All files (*.*)|*.*";
        if (dialog.ShowDialog() == true)
        {
            TxtCommentExcelPath.Text = dialog.FileName;
        }
    }

    private void ChkCommentUseMedia_Checked(object sender, RoutedEventArgs e)
    {
        if (PanelCommentMedia != null) PanelCommentMedia.Visibility = Visibility.Visible;
    }

    private void ChkCommentUseMedia_Unchecked(object sender, RoutedEventArgs e)
    {
        if (PanelCommentMedia != null) PanelCommentMedia.Visibility = Visibility.Collapsed;
    }

    private void BtnSelectCommentMedia_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog();
        dialog.Title = "Chọn file hình ảnh/video cho Comment";
        dialog.Multiselect = true;
        dialog.Filter = "Image/Video Files|*.jpg;*.jpeg;*.png;*.mp4|All files (*.*)|*.*";
        if (dialog.ShowDialog() == true)
        {
            TxtCommentMediaPath.Text = string.Join("\n", dialog.FileNames);
        }
    }

    private System.Threading.CancellationTokenSource? _postCts;
    private System.Threading.CancellationTokenSource? _connectCts;
    private System.Threading.CancellationTokenSource? _commentCts;
    private System.Threading.CancellationTokenSource? _nurtureCts;

    private async void BtnStartPost_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null || vm.SelectedAccountsForPost.Count == 0)
        {
            MessageBox.Show("Vui lòng chọn ít nhất một tài khoản để đăng bài.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        int threadCount = 1;
        if (!int.TryParse(TxtThreadCount.Text, out threadCount) || threadCount < 1)
        {
            threadCount = 1;
        }

        int delayMin = 10;
        int delayMax = 20;
        int.TryParse(TxtDelayMin.Text, out delayMin);
        int.TryParse(TxtDelayMax.Text, out delayMax);

        string contentSource = RbSourceGemini.IsChecked == true ? "2" : "1";
        string apiPrompt = TxtGeminiPrompt.Text.Trim();
        string hashtagText = ChkUseHashtag.IsChecked == true ? TxtHashtags.Text.Trim() : "";
        string mediaPathsStr = "";
        if (ChkUseMedia.IsChecked == true)
        {
            mediaPathsStr = string.Join("|", TxtMediaPath.Text.Split(new[] { '\n', '\r' }, System.StringSplitOptions.RemoveEmptyEntries));
        }
        string excelPath = TxtExcelPath != null ? TxtExcelPath.Text.Trim() : "";

        int loopCount = 1;
        if (ChkPostLoop.IsChecked == true && int.TryParse(TxtPostLoopCount.Text, out int parsedLoop) && parsedLoop > 0)
        {
            loopCount = parsedLoop;
        }

        TxtLogs.Text = $"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu tiến trình đăng bài với {threadCount} luồng...\n";
        TxtLogs.ScrollToEnd();

        _postCts = new System.Threading.CancellationTokenSource();
        var token = _postCts.Token;

        var random = new Random();
        
        int totalAccounts = vm.SelectedAccountsForPost.Count * loopCount;
        int completedAccounts = 0;
        
        PanelProgress.Visibility = Visibility.Visible;
        TxtPostProgress.Text = $"Đang chạy: 0/{totalAccounts}";
        BtnStartPost.IsEnabled = false;

        for (int loopIndex = 0; loopIndex < loopCount; loopIndex++)
        {
            if (token.IsCancellationRequested) break;

            if (loopCount > 1)
            {
                TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu vòng lặp thứ {loopIndex + 1}/{loopCount}...\n");
                TxtLogs.ScrollToEnd();
            }

            var semaphore = new System.Threading.SemaphoreSlim(threadCount);
            var tasks = new System.Collections.Generic.List<System.Threading.Tasks.Task>();

            foreach (var acc in vm.SelectedAccountsForPost)
            {
                acc.PostProcessStatus = "Chờ";
            }

            foreach (var acc in vm.SelectedAccountsForPost)
            {
                await semaphore.WaitAsync();

                if (token.IsCancellationRequested)
                {
                    semaphore.Release();
                    break;
                }

                tasks.Add(System.Threading.Tasks.Task.Run(async () =>
                {
                    try
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đang chạy"; });
                        
                        string pythonScriptDir = System.AppDomain.CurrentDomain.BaseDirectory;
                    if (!System.IO.File.Exists(System.IO.Path.Combine(pythonScriptDir, "main.py")))
                    {
                        pythonScriptDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(pythonScriptDir, @"..\..\..\.."));
                    }
                    
                    string safeApiPrompt = "\"" + apiPrompt.Replace("\"", "\\\"") + "\"";
                    string safeHashtagText = "\"" + hashtagText.Replace("\"", "\\\"") + "\"";
                    string safeMediaPathsStr = "\"" + mediaPathsStr.Replace("\"", "\\\"") + "\"";
                    string safeExcelPath = "\"" + excelPath.Replace("\"", "\\\"") + "\"";

                    var startInfo = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = $"-u main.py post_thread {acc.Uid} \"{contentSource}\" {safeApiPrompt} {safeHashtagText} {safeMediaPathsStr} {safeExcelPath}",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = System.Text.Encoding.UTF8,
                        StandardErrorEncoding = System.Text.Encoding.UTF8,
                        WorkingDirectory = pythonScriptDir
                    };
                    startInfo.Environment["AUTO_GET_COOKIE_THREADS"] = GetAutoCookieSetting();

                    using (var process = new System.Diagnostics.Process { StartInfo = startInfo })
                    {
                        process.OutputDataReceived += (s, ev) =>
                        {
                            if (!string.IsNullOrEmpty(ev.Data))
                            {
                                HandleCookieUpdateMessage(ev.Data);
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}]: {ev.Data}\n");
                                    TxtLogs.ScrollToEnd();
                                });
                            }
                        };

                        process.Start();
                        process.BeginOutputReadLine();

                        while (!process.HasExited)
                        {
                            if (token.IsCancellationRequested)
                            {
                                try { process.Kill(); } catch { }
                                break;
                            }
                            await System.Threading.Tasks.Task.Delay(500);
                        }
                    }

                    if (token.IsCancellationRequested)
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đã dừng"; });
                    }
                    else
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Xong"; });
                    }
                    
                    if (!token.IsCancellationRequested)
                    {
                        int delaySec = random.Next(delayMin, delayMax + 1);
                        Application.Current.Dispatcher.Invoke(() =>
                        {
                            TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Đợi {delaySec}s...\n");
                            TxtLogs.ScrollToEnd();
                        });
                        await System.Threading.Tasks.Task.Delay(delaySec * 1000, token);
                    }
                }
                catch (System.OperationCanceledException)
                {
                }
                catch (Exception ex)
                {
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}] Lỗi: {ex.Message}\n");
                        TxtLogs.ScrollToEnd();
                    });
                }
                finally
                {
                    semaphore.Release();
                    System.Threading.Interlocked.Increment(ref completedAccounts);
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        TxtPostProgress.Text = $"Đang chạy: {completedAccounts}/{totalAccounts}";
                    });
                }
            }));
        }

        await System.Threading.Tasks.Task.WhenAll(tasks);
        Application.Current.Dispatcher.Invoke(() => {
            if (DataContext is ViewModels.MainViewModel mainViewModel)
            {
                mainViewModel.LoadData();
            }
        });
        } // End loopCount

        PanelProgress.Visibility = Visibility.Collapsed;
        BtnStartPost.IsEnabled = true;

        if (token.IsCancellationRequested)
        {
            TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Tiến trình bị hủy bởi người dùng.\n");
            System.Windows.MessageBox.Show("Tiến trình đăng bài đã được dừng lại!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        else
        {
            TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Hoàn thành tất cả tác vụ đăng bài.\n");
            System.Windows.MessageBox.Show("Đã hoàn thành đăng bài cho tất cả tài khoản!", "Hoàn tất", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        TxtLogs.ScrollToEnd();
    }

    private void BtnStopPost_Click(object sender, RoutedEventArgs e)
    {
        if (_postCts != null && !_postCts.IsCancellationRequested)
        {
            _postCts.Cancel();
            TxtLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Đang dừng tiến trình đăng bài...\n");
            TxtLogs.ScrollToEnd();
        }
    }


    private void MenuItem_Copy_Click(object sender, RoutedEventArgs e)
    {
        var selectedItems = DgAccounts.SelectedItems.Cast<Models.AccountModel>().ToList();
        if (selectedItems.Count == 0) return;

        var sb = new System.Text.StringBuilder();
        foreach (var acc in selectedItems)
        {
            var parts = new System.Collections.Generic.List<string>
            {
                acc.Uid ?? "",
                acc.Password ?? "",
                acc.Cookie ?? "",
                acc.Token ?? "",
                acc.Email ?? "",
                acc.PassEmail ?? "",
                acc.TwoFA ?? "",
                acc.Proxy ?? "",
                acc.UserAgent ?? ""
            };

            // Loại bỏ các trường rỗng ở cuối để chuỗi copy gọn gàng
            while (parts.Count > 0 && string.IsNullOrEmpty(parts.Last()))
            {
                parts.RemoveAt(parts.Count - 1);
            }

            sb.AppendLine(string.Join("|", parts));
        }

        System.Windows.Clipboard.SetText(sb.ToString().TrimEnd());
        System.Windows.MessageBox.Show("Đã copy dữ liệu vào Clipboard!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
    }

    private void BtnSelectAccountsForComment_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null) return;
        
        var selectWindow = new SelectAccountWindow(vm.Accounts);
        selectWindow.Owner = this;
        if (selectWindow.ShowDialog() == true)
        {
            var selected = selectWindow.SelectedAccounts;
            foreach (var acc in selected)
            {
                if (!vm.SelectedAccountsForComment.Any(a => a.Uid == acc.Uid))
                {
                    vm.SelectedAccountsForComment.Add(acc);
                }
            }
            
            for (int i = 0; i < vm.SelectedAccountsForComment.Count; i++)
            {
                vm.SelectedAccountsForComment[i].Index = i + 1;
            }
        }
    }

    private void BtnRemoveCommentAccount_Click(object sender, RoutedEventArgs e)
    {
        var button = sender as Button;
        if (button != null)
        {
            var item = button.DataContext as Models.AccountModel;
            if (item != null)
            {
                var vm = this.DataContext as MainViewModel;
                if (vm != null)
                {
                    vm.SelectedAccountsForComment.Remove(item);
                    for (int i = 0; i < vm.SelectedAccountsForComment.Count; i++)
                    {
                        vm.SelectedAccountsForComment[i].Index = i + 1;
                    }
                }
            }
        }
    }

    private async void BtnStartComment_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null || vm.SelectedAccountsForComment.Count == 0)
        {
            MessageBox.Show("Vui lòng chọn ít nhất một tài khoản để comment.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        int threadCount = 1;
        if (!int.TryParse(TxtCommentThreadCount.Text, out threadCount) || threadCount < 1) threadCount = 1;

        int numComments = 1;
        if (TxtCommentNum != null && !int.TryParse(TxtCommentNum.Text, out numComments) || numComments < 1) numComments = 1;

        int delayMin = 10, delayMax = 20;
        int.TryParse(TxtCommentDelayMin.Text, out delayMin);
        int.TryParse(TxtCommentDelayMax.Text, out delayMax);

        string mode = RbCommentNewfeed.IsChecked == true ? "1" : "2";
        string keywords = "";

        string contentSource = "1";
        string apiPrompt = "";
        string excelPath = TxtCommentExcelPath != null ? TxtCommentExcelPath.Text.Trim() : "";
        string mediaPathsStr = "";
        if (ChkCommentUseMedia != null && ChkCommentUseMedia.IsChecked == true && TxtCommentMediaPath != null)
        {
            mediaPathsStr = string.Join("|", TxtCommentMediaPath.Text.Split(new[] { '\n', '\r' }, System.StringSplitOptions.RemoveEmptyEntries));
        }

        int loopCount = 1;
        if (ChkCommentLoop.IsChecked == true && int.TryParse(TxtCommentLoopCount.Text, out int parsedLoop) && parsedLoop > 0)
        {
            loopCount = parsedLoop;
        }

        TxtLogsComment.Text = $"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu tiến trình comment với {threadCount} luồng...\n";
        TxtLogsComment.ScrollToEnd();

        _commentCts = new System.Threading.CancellationTokenSource();
        var token = _commentCts.Token;

        var random = new Random();
        
        int totalAccounts = vm.SelectedAccountsForComment.Count * loopCount;
        int completedAccounts = 0;
        
        if (PanelProgressComment != null) PanelProgressComment.Visibility = Visibility.Visible;
        if (TxtCommentProgress != null) TxtCommentProgress.Text = $"Đang chạy: 0/{totalAccounts}";
        if (BtnStartComment != null) BtnStartComment.IsEnabled = false;

        for (int loopIndex = 0; loopIndex < loopCount; loopIndex++)
        {
            if (token.IsCancellationRequested) break;

            if (loopCount > 1)
            {
                TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu vòng lặp thứ {loopIndex + 1}/{loopCount}...\n");
                TxtLogsComment.ScrollToEnd();
            }

            var semaphore = new System.Threading.SemaphoreSlim(threadCount);
            var tasks = new System.Collections.Generic.List<System.Threading.Tasks.Task>();

            foreach (var acc in vm.SelectedAccountsForComment)
            {
                acc.PostProcessStatus = "Chờ";
            }

            foreach (var acc in vm.SelectedAccountsForComment)
            {
                await semaphore.WaitAsync();

                if (token.IsCancellationRequested)
                {
                    semaphore.Release();
                    break;
                }

                tasks.Add(System.Threading.Tasks.Task.Run(async () =>
                {
                    try
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đang chạy"; });
                        
                        string pythonScriptDir = System.AppDomain.CurrentDomain.BaseDirectory;
                    if (!System.IO.File.Exists(System.IO.Path.Combine(pythonScriptDir, "main.py")))
                    {
                        pythonScriptDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(pythonScriptDir, @"..\..\..\.."));
                    }
                    
                    string safeKeywords = "\"" + keywords.Replace("\"", "\\\"") + "\"";
                    string safeApiPrompt = "\"" + apiPrompt.Replace("\"", "\\\"") + "\"";
                    string safeMediaPathsStr = "\"" + mediaPathsStr.Replace("\"", "\\\"") + "\"";
                    string safeExcelPath = "\"" + excelPath.Replace("\"", "\\\"") + "\"";

                    var startInfo = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = $"-u main.py comment_thread {acc.Uid} {mode} {numComments} {delayMin} {delayMax} {safeKeywords} \"{contentSource}\" {safeApiPrompt} {safeMediaPathsStr} {safeExcelPath}",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = System.Text.Encoding.UTF8,
                        StandardErrorEncoding = System.Text.Encoding.UTF8,
                        WorkingDirectory = pythonScriptDir
                    };
                    startInfo.Environment["AUTO_GET_COOKIE_THREADS"] = GetAutoCookieSetting();

                    using (var process = new System.Diagnostics.Process { StartInfo = startInfo })
                    {
                        process.OutputDataReceived += (s, ev) =>
                        {
                            if (!string.IsNullOrEmpty(ev.Data))
                            {
                                HandleCookieUpdateMessage(ev.Data);
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}]: {ev.Data}\n");
                                    TxtLogsComment.ScrollToEnd();
                                });
                            }
                        };
                        
                        process.ErrorDataReceived += (s, ev) =>
                        {
                            if (!string.IsNullOrEmpty(ev.Data))
                            {
                                HandleCookieUpdateMessage(ev.Data);
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [ERROR {acc.Uid}]: {ev.Data}\n");
                                    TxtLogsComment.ScrollToEnd();
                                });
                            }
                        };

                        process.Start();
                        process.BeginOutputReadLine();
                        process.BeginErrorReadLine();

                        while (!process.HasExited)
                        {
                            if (token.IsCancellationRequested)
                            {
                                try { process.Kill(); } catch { }
                                break;
                            }
                            await System.Threading.Tasks.Task.Delay(500);
                        }
                    }

                    if (token.IsCancellationRequested)
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đã dừng"; });
                    }
                    else
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Xong"; });
                    }
                    
                    if (!token.IsCancellationRequested)
                    {
                        int delaySec = random.Next(delayMin, delayMax + 1);
                        Application.Current.Dispatcher.Invoke(() =>
                        {
                            TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Đợi {delaySec}s...\n");
                            TxtLogsComment.ScrollToEnd();
                        });
                        await System.Threading.Tasks.Task.Delay(delaySec * 1000, token);
                    }
                }
                catch (System.OperationCanceledException)
                {
                }
                catch (Exception ex)
                {
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}] Lỗi: {ex.Message}\n");
                        TxtLogsComment.ScrollToEnd();
                    });
                }
                finally
                {
                    semaphore.Release();
                    System.Threading.Interlocked.Increment(ref completedAccounts);
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        if (TxtCommentProgress != null) TxtCommentProgress.Text = $"Đang chạy: {completedAccounts}/{totalAccounts}";
                    });
                }
            }));
        }

        await System.Threading.Tasks.Task.WhenAll(tasks);
        Application.Current.Dispatcher.Invoke(() => {
            if (DataContext is ViewModels.MainViewModel mainViewModel)
            {
                mainViewModel.LoadData();
            }
        });
        } // End loopCount

        if (PanelProgressComment != null) PanelProgressComment.Visibility = Visibility.Collapsed;
        if (BtnStartComment != null) BtnStartComment.IsEnabled = true;

        if (token.IsCancellationRequested)
        {
            TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Tiến trình bị hủy bởi người dùng.\n");
            System.Windows.MessageBox.Show("Tiến trình comment dạo đã được dừng lại!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        else
        {
            TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Hoàn thành tất cả tác vụ comment.\n");
            System.Windows.MessageBox.Show("Đã hoàn thành comment dạo cho tất cả tài khoản!", "Hoàn tất", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        TxtLogsComment.ScrollToEnd();
    }

    private void BtnStopComment_Click(object sender, RoutedEventArgs e)
    {
        if (_commentCts != null && !_commentCts.IsCancellationRequested)
        {
            _commentCts.Cancel();
            TxtLogsComment.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Đang dừng tiến trình comment dạo...\n");
            TxtLogsComment.ScrollToEnd();
        }
    }

    private void MenuItem_Nurture_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null) return;
        vm.SelectedAccountsForNurture.Clear();
        foreach (var acc in vm.Accounts)
        {
            if (acc.IsSelected)
            {
                vm.SelectedAccountsForNurture.Add(acc);
            }
        }
        for (int i = 0; i < vm.SelectedAccountsForNurture.Count; i++)
        {
            vm.SelectedAccountsForNurture[i].Index = i + 1;
        }
        System.Windows.MessageBox.Show($"Đã chọn {vm.SelectedAccountsForNurture.Count} tài khoản để nuôi.", "Thành công", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
    }

    private void BtnSelectAccountsForNurture_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null) return;
        
        var selectWindow = new SelectAccountWindow(vm.Accounts);
        selectWindow.Owner = this;
        if (selectWindow.ShowDialog() == true)
        {
            var selected = selectWindow.SelectedAccounts;
            foreach (var acc in selected)
            {
                if (!vm.SelectedAccountsForNurture.Any(a => a.Uid == acc.Uid))
                {
                    vm.SelectedAccountsForNurture.Add(acc);
                }
            }
            
            // Cập nhật lại số thứ tự
            for (int i = 0; i < vm.SelectedAccountsForNurture.Count; i++)
            {
                vm.SelectedAccountsForNurture[i].Index = i + 1;
            }
        }
    }

    private void BtnRemoveNurtureAccount_Click(object sender, RoutedEventArgs e)
    {
        var button = sender as Button;
        if (button != null)
        {
            var item = button.DataContext as Models.AccountModel;
            if (item != null)
            {
                var vm = this.DataContext as MainViewModel;
                if (vm != null)
                {
                    vm.SelectedAccountsForNurture.Remove(item);
                    for (int i = 0; i < vm.SelectedAccountsForNurture.Count; i++)
                    {
                        vm.SelectedAccountsForNurture[i].Index = i + 1;
                    }
                }
            }
        }
    }

    private async void BtnStartNurture_Click(object sender, RoutedEventArgs e)
    {
        var vm = this.DataContext as MainViewModel;
        if (vm == null || vm.SelectedAccountsForNurture.Count == 0)
        {
            System.Windows.MessageBox.Show("Vui lòng chọn ít nhất một tài khoản.", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
            return;
        }

        int maxThreads = 1;
        if (!int.TryParse(TxtNurtureThreadCount.Text, out maxThreads) || maxThreads <= 0) maxThreads = 1;

        int isScroll = ChkScrollNewsfeed.IsChecked == true ? 1 : 0;

        int isLike = ChkLikePost.IsChecked == true ? 1 : 0;
        int likeDelayMin = 10, likeDelayMax = 30;
        if (isLike == 1)
        {
            if (!int.TryParse(TxtLikeDelayMin.Text, out likeDelayMin)) likeDelayMin = 10;
            if (!int.TryParse(TxtLikeDelayMax.Text, out likeDelayMax)) likeDelayMax = 30;
            if (likeDelayMin > likeDelayMax) likeDelayMin = likeDelayMax;
        }

        int isReadNotif = ChkReadNotifications.IsChecked == true ? 1 : 0;
        int notifCount = 2;
        if (isReadNotif == 1 && (!int.TryParse(TxtNotificationCount.Text, out notifCount) || notifCount <= 0)) notifCount = 2;

        int totalMins = 30;
        if (!int.TryParse(TxtTotalNurtureMinutes.Text, out totalMins) || totalMins <= 0) totalMins = 30;

        int loopCount = 1;
        if (ChkNurtureLoop.IsChecked == true && int.TryParse(TxtNurtureLoopCount.Text, out int parsedLoop) && parsedLoop > 0)
        {
            loopCount = parsedLoop;
        }

        _nurtureCts = new System.Threading.CancellationTokenSource();
        var token = _nurtureCts.Token;

        TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu chạy Nuôi tài khoản với {maxThreads} luồng.\n");
        TxtNurtureLogs.ScrollToEnd();

        int totalAccounts = vm.SelectedAccountsForNurture.Count * loopCount;
        int completedAccounts = 0;
        
        if (PanelProgressNurture != null) PanelProgressNurture.Visibility = Visibility.Visible;
        if (TxtNurtureProgress != null) TxtNurtureProgress.Text = $"Đang chạy: 0/{totalAccounts}";
        if (BtnStartNurture != null) BtnStartNurture.IsEnabled = false;

        for (int loopIndex = 0; loopIndex < loopCount; loopIndex++)
        {
            if (token.IsCancellationRequested) break;

            if (loopCount > 1)
            {
                TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Bắt đầu vòng lặp thứ {loopIndex + 1}/{loopCount}...\n");
                TxtNurtureLogs.ScrollToEnd();
            }

            var semaphore = new System.Threading.SemaphoreSlim(maxThreads);
            var tasks = new System.Collections.Generic.List<System.Threading.Tasks.Task>();

            foreach (var acc in vm.SelectedAccountsForNurture)
            {
                acc.PostProcessStatus = "Chờ";
            }

            foreach (var acc in vm.SelectedAccountsForNurture)
            {
                await semaphore.WaitAsync();

                if (token.IsCancellationRequested)
                {
                    semaphore.Release();
                    break;
                }

                tasks.Add(System.Threading.Tasks.Task.Run(async () =>
                {
                    try
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đang chạy"; });
                        
                        string pythonScriptDir = System.AppDomain.CurrentDomain.BaseDirectory;
                    if (!System.IO.File.Exists(System.IO.Path.Combine(pythonScriptDir, "main.py")))
                    {
                        pythonScriptDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(pythonScriptDir, @"..\..\..\.."));
                    }

                    // python -u main.py farm_thread <uid> <is_scroll> <is_like> <like_delay_min> <like_delay_max> <is_read_notif> <notif_count> <total_mins>
                    string args = $"-u main.py farm_thread {acc.Uid} {isScroll} {isLike} {likeDelayMin} {likeDelayMax} {isReadNotif} {notifCount} {totalMins}";

                    var startInfo = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = args,
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = System.Text.Encoding.UTF8,
                        StandardErrorEncoding = System.Text.Encoding.UTF8,
                        WorkingDirectory = pythonScriptDir
                    };
                    startInfo.Environment["AUTO_GET_COOKIE_THREADS"] = GetAutoCookieSetting();

                    using (var process = new System.Diagnostics.Process { StartInfo = startInfo })
                    {
                        process.OutputDataReceived += (s, ev) =>
                        {
                            if (!string.IsNullOrEmpty(ev.Data))
                            {
                                HandleCookieUpdateMessage(ev.Data);
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}]: {ev.Data}\n");
                                    TxtNurtureLogs.ScrollToEnd();
                                });
                            }
                        };
                        
                        process.ErrorDataReceived += (s, ev) =>
                        {
                            if (!string.IsNullOrEmpty(ev.Data))
                            {
                                HandleCookieUpdateMessage(ev.Data);
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [ERROR {acc.Uid}]: {ev.Data}\n");
                                    TxtNurtureLogs.ScrollToEnd();
                                });
                            }
                        };

                        process.Start();
                        process.BeginOutputReadLine();
                        process.BeginErrorReadLine();

                        while (!process.HasExited)
                        {
                            if (token.IsCancellationRequested)
                            {
                                try { process.Kill(); } catch { }
                                break;
                            }
                            await System.Threading.Tasks.Task.Delay(500);
                        }
                    }

                    if (token.IsCancellationRequested)
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Đã dừng"; });
                    }
                    else
                    {
                        Application.Current.Dispatcher.Invoke(() => { acc.PostProcessStatus = "Xong"; });
                    }
                }
                catch (Exception ex)
                {
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [{acc.Uid}] Lỗi: {ex.Message}\n");
                        TxtNurtureLogs.ScrollToEnd();
                    });
                }
                finally
                {
                    semaphore.Release();
                    System.Threading.Interlocked.Increment(ref completedAccounts);
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        if (TxtNurtureProgress != null) TxtNurtureProgress.Text = $"Đang chạy: {completedAccounts}/{totalAccounts}";
                    });
                }
            }));
        }

        await System.Threading.Tasks.Task.WhenAll(tasks);
        Application.Current.Dispatcher.Invoke(() => {
            if (DataContext is ViewModels.MainViewModel mainViewModel)
            {
                mainViewModel.LoadData();
            }
        });
        } // End loopCount

        if (PanelProgressNurture != null) PanelProgressNurture.Visibility = Visibility.Collapsed;
        if (BtnStartNurture != null) BtnStartNurture.IsEnabled = true;

        if (token.IsCancellationRequested)
        {
            TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Tiến trình bị hủy bởi người dùng.\n");
            System.Windows.MessageBox.Show("Tiến trình nuôi tài khoản đã được dừng lại!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        else
        {
            TxtNurtureLogs.AppendText($"[{DateTime.Now.ToString("HH:mm:ss")}] [System]: Hoàn thành tất cả tác vụ nuôi tài khoản.\n");
            System.Windows.MessageBox.Show("Đã hoàn thành nuôi tất cả tài khoản!", "Hoàn tất", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        TxtNurtureLogs.ScrollToEnd();
    }

    private void BtnStopNurture_Click(object sender, RoutedEventArgs e)
    {
        if (_nurtureCts != null)
        {
            _nurtureCts.Cancel();
            BtnStartNurture.IsEnabled = true;
        }
    }

    private string GetAutoCookieSetting()
    {
        try
        {
            string settingsFile = System.IO.Path.Combine(System.AppDomain.CurrentDomain.BaseDirectory, "settings.json");
            if (System.IO.File.Exists(settingsFile))
            {
                var json = System.IO.File.ReadAllText(settingsFile);
                var settings = System.Text.Json.JsonSerializer.Deserialize<AppSettings>(json);
                if (settings != null && settings.AutoGetCookieThreads) return "1";
            }
        }
        catch { }
        return "0";
    }

    private void HandleCookieUpdateMessage(string message)
    {
        if (message.StartsWith("[UPDATE_COOKIE_THREADS]"))
        {
            try
            {
                var parts = message.Replace("[UPDATE_COOKIE_THREADS]", "").Trim().Split('|');
                if (parts.Length >= 2)
                {
                    string uid = parts[0];
                    string cookieStr = parts[1];
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        var vm = this.DataContext as MainViewModel;
                        if (vm != null)
                        {
                            var acc = vm.Accounts.FirstOrDefault(a => a.Uid == uid);
                            if (acc != null)
                            {
                                acc.CookieThreads = cookieStr;
                                vm.SaveData();
                            }
                        }
                    });
                }
            }
            catch { }
        }
    }
}
