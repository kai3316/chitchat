import 'package:flutter/material.dart';

class SettingsService extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.dark;
  String _deviceName = 'My Device';
  bool _notificationSound = true;

  ThemeMode get themeMode => _themeMode;
  String get deviceName => _deviceName;

  bool get isDarkMode => _themeMode == ThemeMode.dark;
  bool get notificationSound => _notificationSound;

  void setThemeMode(ThemeMode mode) {
    _themeMode = mode;
    notifyListeners();
  }

  void toggleTheme() {
    _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
  }

  void setDeviceName(String name) {
    _deviceName = name.trim().isEmpty ? 'My Device' : name.trim();
    notifyListeners();
  }

  void toggleNotificationSound() {
    _notificationSound = !_notificationSound;
    notifyListeners();
  }

  void setNotificationSound(bool value) {
    _notificationSound = value;
    notifyListeners();
  }
}
