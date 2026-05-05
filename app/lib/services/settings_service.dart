import 'package:flutter/material.dart';

class SettingsService extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.dark;
  String _deviceName = 'My Device';

  ThemeMode get themeMode => _themeMode;
  String get deviceName => _deviceName;

  bool get isDarkMode => _themeMode == ThemeMode.dark;

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
}
