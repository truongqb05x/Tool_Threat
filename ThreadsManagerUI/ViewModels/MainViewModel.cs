using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using ThreadsManagerUI.Models;

namespace ThreadsManagerUI.ViewModels
{
    public class MainViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<AccountModel> Accounts { get; set; }
        public ObservableCollection<AccountModel> SelectedAccountsForPost { get; set; }
        public ObservableCollection<AccountModel> SelectedAccountsForConnect { get; set; }
        public ObservableCollection<AccountModel> SelectedAccountsForComment { get; set; }
        public ObservableCollection<AccountModel> SelectedAccountsForNurture { get; set; }

        private int _totalAccounts;
        public int TotalAccounts
        {
            get => _totalAccounts;
            set { _totalAccounts = value; OnPropertyChanged(); }
        }

        private int _liveAccounts;
        public int LiveAccounts
        {
            get => _liveAccounts;
            set { _liveAccounts = value; OnPropertyChanged(); }
        }

        private int _deadAccounts;
        public int DeadAccounts
        {
            get => _deadAccounts;
            set { _deadAccounts = value; OnPropertyChanged(); }
        }

        public MainViewModel()
        {
            Accounts = new ObservableCollection<AccountModel>();
            SelectedAccountsForPost = new ObservableCollection<AccountModel>();
            SelectedAccountsForConnect = new ObservableCollection<AccountModel>();
            SelectedAccountsForComment = new ObservableCollection<AccountModel>();
            SelectedAccountsForNurture = new ObservableCollection<AccountModel>();
            LoadData();
            
            Accounts.CollectionChanged += (s, e) => {
                if (e.NewItems != null)
                {
                    foreach (AccountModel newItem in e.NewItems)
                    {
                        newItem.PropertyChanged += (sender, args) => {
                            if (args.PropertyName != nameof(AccountModel.IsSelected) && 
                                args.PropertyName != nameof(AccountModel.PostProcessStatus))
                                SaveData();
                        };
                    }
                }
                UpdateStats();
                SaveData();
            };
        }

        private string GetDataFilePath()
        {
            string devPath = System.IO.Path.GetFullPath(System.IO.Path.Combine(System.AppDomain.CurrentDomain.BaseDirectory, @"..\..\..\..\resources\account.txt"));
            if (System.IO.File.Exists(devPath)) return devPath;
            return "account.txt"; // Fallback
        }

        private bool _isLoading = false;

        public void LoadData()
        {
            _isLoading = true;
            try
            {
                Accounts.Clear();
                string path = GetDataFilePath();
                if (System.IO.File.Exists(path))
                {
                    var lines = System.IO.File.ReadAllLines(path);
                    int index = 1;
                    foreach (var line in lines)
                    {
                        if (string.IsNullOrWhiteSpace(line)) continue;
                        var parts = line.Split('|');
                        var acc = new AccountModel
                        {
                            Index = index++,
                            Uid = parts.Length > 0 ? parts[0] : "",
                            Password = parts.Length > 1 ? parts[1] : "",
                            TwoFA = parts.Length > 2 ? parts[2] : "",
                            Cookie = parts.Length > 3 ? parts[3] : "",
                            CookieThreads = parts.Length > 4 ? parts[4] : "",
                            Token = parts.Length > 5 ? parts[5] : "",
                            Email = parts.Length > 6 ? parts[6] : "",
                            PassEmail = parts.Length > 7 ? parts[7] : "",
                            Proxy = parts.Length > 8 ? parts[8] : "",
                            UserAgent = parts.Length > 9 ? parts[9] : "",
                            Status = parts.Length > 10 ? parts[10] : "Live"
                        };
                        
                        acc.PropertyChanged += (s, e) => {
                            if (e.PropertyName != nameof(AccountModel.IsSelected) && 
                                e.PropertyName != nameof(AccountModel.PostProcessStatus))
                            {
                                SaveData();
                            }
                        };
                        Accounts.Add(acc);
                    }
                }
                UpdateStats();
            }
            finally
            {
                _isLoading = false;
            }
        }

        public void SaveData()
        {
            if (_isLoading) return;
            string path = GetDataFilePath();
            var lines = new System.Collections.Generic.List<string>();
            foreach (var acc in Accounts)
            {
                var parts = new System.Collections.Generic.List<string>
                {
                    acc.Uid ?? "",
                    acc.Password ?? "",
                    acc.TwoFA ?? "",
                    acc.Cookie ?? "",
                    acc.CookieThreads ?? "",
                    acc.Token ?? "",
                    acc.Email ?? "",
                    acc.PassEmail ?? "",
                    acc.Proxy ?? "",
                    acc.UserAgent ?? "",
                    acc.Status ?? "Live"
                };

                // Loại bỏ các phần tử rỗng ở cuối (giống như copy)
                while (parts.Count > 0 && string.IsNullOrEmpty(parts[^1]))
                {
                    parts.RemoveAt(parts.Count - 1);
                }

                lines.Add(string.Join("|", parts));
            }
            
            try
            {
                System.IO.File.WriteAllLines(path, lines);
            }
            catch { }
        }

        public void UpdateStats()
        {
            TotalAccounts = Accounts.Count;
            int liveCount = 0;
            int deadCount = 0;
            foreach(var acc in Accounts) {
                if (acc.Status == "Live") liveCount++;
                else if (acc.Status == "Die") deadCount++;
            }
            LiveAccounts = liveCount;
            DeadAccounts = deadCount;
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string name = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
    }
}
