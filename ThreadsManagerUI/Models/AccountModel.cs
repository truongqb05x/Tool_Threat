using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace ThreadsManagerUI.Models
{
    public class AccountModel : INotifyPropertyChanged
    {
        private bool _isSelected;
        private int _index;
        private string _uid;
        private string _password;
        private string _cookie;
        private string _cookieThreads;
        private string _proxy;
        private string _status;
        private string _notes;
        private string _token;
        private string _email;
        private string _passEmail;
        private string _twoFA;
        private string _userAgent;

        public bool IsSelected
        {
            get => _isSelected;
            set { _isSelected = value; OnPropertyChanged(); }
        }

        public int Index
        {
            get => _index;
            set { _index = value; OnPropertyChanged(); }
        }

        public string Uid
        {
            get => _uid;
            set { _uid = value; OnPropertyChanged(); }
        }

        public string Password
        {
            get => _password;
            set { _password = value; OnPropertyChanged(); }
        }

        public string Cookie
        {
            get => _cookie;
            set { _cookie = value; OnPropertyChanged(); }
        }

        public string CookieThreads
        {
            get => _cookieThreads;
            set { _cookieThreads = value; OnPropertyChanged(); }
        }

        public string Token
        {
            get => _token;
            set { _token = value; OnPropertyChanged(); }
        }

        public string Proxy
        {
            get => _proxy;
            set { _proxy = value; OnPropertyChanged(); }
        }

        public string Email
        {
            get => _email;
            set { _email = value; OnPropertyChanged(); }
        }

        public string PassEmail
        {
            get => _passEmail;
            set { _passEmail = value; OnPropertyChanged(); }
        }

        public string TwoFA
        {
            get => _twoFA;
            set { _twoFA = value; OnPropertyChanged(); }
        }

        public string UserAgent
        {
            get => _userAgent;
            set { _userAgent = value; OnPropertyChanged(); }
        }

        public string Status
        {
            get => _status;
            set { _status = value; OnPropertyChanged(); }
        }

        public string Notes
        {
            get => _notes;
            set { _notes = value; OnPropertyChanged(); }
        }

        private string _postProcessStatus = "Chờ";
        public string PostProcessStatus
        {
            get => _postProcessStatus;
            set { _postProcessStatus = value; OnPropertyChanged(); }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string name = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
    }
}
