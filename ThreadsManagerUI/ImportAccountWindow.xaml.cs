using System;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;

namespace ThreadsManagerUI;

public partial class ImportAccountWindow : Window
{
    public ObservableCollection<Models.AccountModel> PreviewAccounts { get; set; } = new ObservableCollection<Models.AccountModel>();

    public ImportAccountWindow()
    {
        InitializeComponent();
        DgPreview.ItemsSource = PreviewAccounts;
    }

    public string InputData
    {
        get => TxtInputData.Text;
        set => TxtInputData.Text = value;
    }

    private void TxtInputData_TextChanged(object sender, TextChangedEventArgs e)
    {
        PreviewAccounts.Clear();
        if (string.IsNullOrWhiteSpace(TxtInputData.Text)) return;

        var lines = TxtInputData.Text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.RemoveEmptyEntries);
        foreach (var line in lines)
        {
            var parts = line.Split('|');
            var acc = new Models.AccountModel();

            // Phân bổ UID và Password luôn là 2 cột đầu tiên
            if (parts.Length > 0) acc.Uid = parts[0].Trim();
            if (parts.Length > 1) acc.Password = parts[1].Trim();

            // Thêm logic tự nhận dạng các phần còn lại
            var unassignedParts = new System.Collections.Generic.List<string>();

            for (int i = 2; i < parts.Length; i++)
            {
                string p = parts[i].Trim();
                if (string.IsNullOrEmpty(p)) continue;

                // Nhận dạng Cookie
                if (p.Contains("sessionid=") || p.Contains("csrftoken=") || (p.Contains("=") && p.Contains(";")))
                {
                    acc.Cookie = p;
                }
                // Nhận dạng Token
                else if (p.StartsWith("EAAB") || p.StartsWith("EAAAAU"))
                {
                    acc.Token = p;
                }
                // Nhận dạng 2FA (thường là chuỗi Base32 dài, chỉ chứa chữ hoa và số)
                else if (p.Length >= 16 && p.Length <= 64 && System.Text.RegularExpressions.Regex.IsMatch(p.ToUpper(), @"^[A-Z2-7]+$"))
                {
                    acc.TwoFA = p;
                }
                // Nhận dạng Email
                else if (p.Contains("@") && p.Contains("."))
                {
                    acc.Email = p;
                }
                else
                {
                    unassignedParts.Add(p);
                }
            }

            // Phân bổ các phần chưa được nhận dạng
            if (unassignedParts.Count > 0 && string.IsNullOrEmpty(acc.PassEmail) && !string.IsNullOrEmpty(acc.Email))
            {
                acc.PassEmail = unassignedParts[0];
            }

            PreviewAccounts.Add(acc);
        }
    }

    private void BtnImport_Click(object sender, RoutedEventArgs e)
    {
        var mainViewModel = (this.Owner as MainWindow)?.DataContext as ViewModels.MainViewModel;
        if (mainViewModel != null && PreviewAccounts.Count > 0)
        {
            foreach (var acc in PreviewAccounts)
            {
                acc.Index = mainViewModel.Accounts.Count + 1;
                acc.Status = "Live"; // Trạng thái mặc định
                mainViewModel.Accounts.Add(acc);
            }
            mainViewModel.TotalAccounts = mainViewModel.Accounts.Count;
        }
        this.Close();
    }
}
