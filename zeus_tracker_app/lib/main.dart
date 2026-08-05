import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_background_service_android/flutter_background_service_android.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeService();
  runApp(const MyApp());
}

Future<void> initializeService() async {
  final service = FlutterBackgroundService();

  await service.configure(
    androidConfiguration: AndroidConfiguration(
      onStart: onStart,
      autoStart: false,
      isForegroundMode: true,
      notificationChannelId: 'zeus_tracking_channel',
      initialNotificationTitle: 'Zeus Rastreio Ativo',
      initialNotificationContent: 'Transmitindo localização em segundo plano...',
      foregroundServiceNotificationId: 888,
    ),
    iosConfiguration: IosConfiguration(
      autoStart: false,
      onForeground: onStart,
      onBackground: onIosBackground,
    ),
  );
}

@pragma('vm:entry-point')
bool onIosBackground(ServiceInstance service) {
  WidgetsFlutterBinding.ensureInitialized();
  return true;
}

@pragma('vm:entry-point')
void onStart(ServiceInstance service) async {
  DartPluginRegistrant.ensureInitialized();

  if (service is AndroidServiceInstance) {
    service.on('setAsForeground').listen((event) {
      service.setAsForegroundService();
    });

    service.on('setAsBackground').listen((event) {
      service.setAsBackgroundService();
    });
  }

  service.on('stopService').listen((event) {
    service.stopSelf();
  });

  // Timer rodando em background a cada 15 segundos
  Timer.periodic(const Duration(seconds: 15), (timer) async {
    if (service is AndroidServiceInstance) {
      if (!await service.isForegroundService()) return;
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      String imei = prefs.getString('imei') ?? 'Douglasgarcia';

      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.best,
      );

      double lat = position.latitude;
      double lon = position.longitude;
      double speed = position.speed * 3.6;

      final url = Uri.parse(
        'https://zeusrastreio.onrender.com/api/posicoes?imei=$imei&lat=$lat&lon=$lon&speed=$speed'
      );

      final response = await http.get(url);
      if (response.statusCode == 200) {
        print("Background: Posição enviada com sucesso!");
      }
    } catch (e) {
      print("Background erro: $e");
    }
  });
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Zeus Rastreio App',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const RastreioPage(),
    );
  }
}

class RastreioPage extends StatefulWidget {
  const RastreioPage({super.key});

  @override
  State<RastreioPage> createState() => _RastreioPageState();
}

class _RastreioPageState extends State<RastreioPage> {
  final TextEditingController _imeiController = TextEditingController(text: "Douglasgarcia");
  bool _isTracking = false;
  String _statusMessage = "Pronto para iniciar";

  @override
  void initState() {
    super.initState();
    _checkRunningState();
  }

  void _checkRunningState() async {
    final service = FlutterBackgroundService();
    bool isRunning = await service.isRunning();
    setState(() {
      _isTracking = isRunning;
      _statusMessage = isRunning ? "Rastreando em segundo plano..." : "Pronto para iniciar";
    });
  }

  Future<void> _checkPermissions() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      setState(() => _statusMessage = "Erro: O GPS está desativado.");
      return;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        setState(() => _statusMessage = "Permissão de localização negada.");
        return;
      }
    }
  }

  void _toggleTracking() async {
    final service = FlutterBackgroundService();
    bool isRunning = await service.isRunning();

    if (isRunning) {
      service.invoke("stopService");
      setState(() {
        _isTracking = false;
        _statusMessage = "Rastreamento pausado.";
      });
    } else {
      await _checkPermissions();
      
      // Salva o IMEI nas preferências para o background ler
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('imei', _imeiController.text.trim());

      service.startService();
      setState(() {
        _isTracking = true;
        _statusMessage = "Rastreando em segundo plano (Serviço Ativo)...";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Zeus Rastreio - Profissional')),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _imeiController,
              decoration: const InputDecoration(
                labelText: 'Identificador do Dispositivo (IMEI)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _statusMessage,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: _isTracking ? Colors.green : Colors.grey,
              ),
            ),
            const SizedBox(height: 30),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _isTracking ? Colors.red : Colors.green,
                padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 15),
              ),
              onPressed: _toggleTracking,
              child: Text(
                _isTracking ? 'PARAR RASTREIO' : 'INICIAR RASTREIO',
                style: const TextStyle(fontSize: 18, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
    );
  }
}