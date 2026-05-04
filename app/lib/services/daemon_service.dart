import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class DaemonService extends ChangeNotifier {
  WebSocketChannel? _channel;
  int _reqId = 0;
  final Map<int, Completer<Map<String, dynamic>>> _pending = {};
  bool _connected = false;

  // Cached state
  Map<String, dynamic> _status = {};
  List<Map<String, dynamic>> _contacts = [];
  Map<String, List<Map<String, dynamic>>> _conversations = {};
  final StreamController<Map<String, dynamic>> _events = StreamController.broadcast();

  bool get isConnected => _connected;
  Map<String, dynamic> get status => _status;
  List<Map<String, dynamic>> get contacts => _contacts;
  Stream<Map<String, dynamic>> get events => _events.stream;

  void connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:9876'));
      _connected = true;
      _channel!.stream.listen(_onMessage, onDone: _onDisconnect, onError: (_) => _onDisconnect());
      _refreshState();
      notifyListeners();
    } catch (e) {
      _connected = false;
      notifyListeners();
      // Retry connection
      Future.delayed(const Duration(seconds: 2), connect);
    }
  }

  void _onDisconnect() {
    _connected = false;
    _channel = null;
    notifyListeners();
    Future.delayed(const Duration(seconds: 2), connect);
  }

  void _onMessage(dynamic raw) {
    final msg = jsonDecode(raw) as Map<String, dynamic>;
    if (msg.containsKey('event')) {
      _events.add(msg);
      _handleEvent(msg['event'] as String, msg['data'] as Map<String, dynamic>? ?? {});
    } else if (msg.containsKey('result') && msg.containsKey('id')) {
      final completer = _pending.remove(msg['id'] as int);
      if (completer != null) {
        completer.complete(msg['result'] as Map<String, dynamic>? ?? {});
      }
    }
  }

  void _handleEvent(String event, Map<String, dynamic> data) {
    switch (event) {
      case 'message_received':
        final peerId = data['peer_id'] as String;
        _conversations.putIfAbsent(peerId, () => []);
        _conversations[peerId]!.add(data);
        _refreshContacts();
        break;
      case 'peer_online':
      case 'peer_offline':
        _refreshContacts();
        break;
      case 'typing':
      case 'presence':
      case 'reaction':
      case 'message_delivered':
        break;
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>> _call(String method, Map<String, dynamic> params) async {
    if (!_connected || _channel == null) {
      throw Exception('Not connected to daemon');
    }
    final id = ++_reqId;
    final completer = Completer<Map<String, dynamic>>();
    _pending[id] = completer;
    _channel!.sink.add(jsonEncode({'method': method, 'params': params, 'id': id}));
    return completer.future.timeout(const Duration(seconds: 10));
  }

  void _sendNotification(String method, Map<String, dynamic> params) {
    if (!_connected || _channel == null) return;
    _channel!.sink.add(jsonEncode({'method': method, 'params': params}));
  }

  // ── Public API ──────────────────────────────────────────

  Future<void> _refreshState() async {
    try {
      _status = await _call('get_status', {});
      _contacts = (await _call('get_contacts', {}))['contacts'] as List<Map<String, dynamic>>? ?? [];
      notifyListeners();
    } catch (_) {}
  }

  Future<void> _refreshContacts() async {
    try {
      _contacts = (await _call('get_contacts', {}))['contacts'] as List<Map<String, dynamic>>? ?? [];
      notifyListeners();
    } catch (_) {}
  }

  Future<Map<String, dynamic>> sendMessage(String peerId, String text, {String replyTo = ''}) async {
    return _call('send_message', {
      'peer_id': peerId, 'type': 'chat_text',
      'body': text, 'reply_to': replyTo,
    });
  }

  Future<List<Map<String, dynamic>>> getHistory(String peerId, {int limit = 50}) async {
    final result = await _call('get_history', {'peer_id': peerId, 'limit': limit});
    final msgs = (result['messages'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ?? [];
    _conversations[peerId] = msgs.reversed.toList();
    notifyListeners();
    return _conversations[peerId]!;
  }

  List<Map<String, dynamic>> getMessages(String peerId) {
    return _conversations[peerId] ?? [];
  }

  void sendTyping(String peerId) {
    _sendNotification('send_typing', {'peer_id': peerId});
  }

  void markRead(String peerId) {
    _sendNotification('mark_read', {'peer_id': peerId});
  }

  Future<bool> pairDevice(String peerId, String code) async {
    final result = await _call('pair_device', {'peer_id': peerId, 'code': code});
    return result['ok'] as bool? ?? false;
  }

  void sendReaction(String peerId, String msgId, String emoji) {
    _sendNotification('react', {'peer_id': peerId, 'msg_id': msgId, 'emoji': emoji});
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _events.close();
    super.dispose();
  }
}
