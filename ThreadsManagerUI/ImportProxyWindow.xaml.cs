using System;
using System.Linq;
using System.Windows;

namespace ThreadsManagerUI;

public partial class ImportProxyWindow : Window
{
    public ImportProxyWindow()
    {
        InitializeComponent();
    }

    private void BtnImport_Click(object sender, RoutedEventArgs e)
    {
        var mainViewModel = (this.Owner as MainWindow)?.DataContext as ViewModels.MainViewModel;
        if (mainViewModel == null || mainViewModel.Accounts.Count == 0)
        {
            MessageBox.Show("Không có tài khoản nào để gán proxy!", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        var proxies = TxtProxies.Text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.RemoveEmptyEntries)
                                     .Select(p => p.Trim())
                                     .Where(p => !string.IsNullOrEmpty(p))
                                     .ToList();

        if (proxies.Count == 0)
        {
            MessageBox.Show("Vui lòng nhập danh sách proxy!", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        if (RbSequential.IsChecked == true)
        {
            for (int i = 0; i < mainViewModel.Accounts.Count; i++)
            {
                mainViewModel.Accounts[i].Proxy = proxies[i % proxies.Count];
            }
        }
        else if (RbRandom.IsChecked == true)
        {
            var random = new Random();
            for (int i = 0; i < mainViewModel.Accounts.Count; i++)
            {
                mainViewModel.Accounts[i].Proxy = proxies[random.Next(proxies.Count)];
            }
        }

        MessageBox.Show($"Đã gán {proxies.Count} proxy cho {mainViewModel.Accounts.Count} tài khoản!", "Thành công", MessageBoxButton.OK, MessageBoxImage.Information);
        this.Close();
    }
}
