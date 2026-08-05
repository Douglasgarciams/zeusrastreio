import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Zeus Multimídia & Rastreio',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const MultimidiaRastreioPage(),
    );
  }
}

class MultimidiaRastreioPage extends StatefulWidget {
  const MultimidiaRastreioPage({super.key});

  @override
  State<MultimidiaRastreioPage> createState() => _MultimidiaRastreioPageState();
}

class _MultimidiaRastreioPageState extends State<MultimidiaRastreioPage> {
  final TextEditingController _imeiController = TextEditingController(text: "Douglasgarcia");
  bool _isTracking = false;
  String _statusMessage = "Pronto para iniciar";
  Timer? _locationTimer;

  // Variáveis para Mídia
  final ImagePicker _picker = ImagePicker();
  File? _selectedImage;
  
  late final AudioRecorder _audioRecorder;
  bool _isRecording = false;
  String? _audioPath;

  @override
  void initState() {
    super.initState();
    _audioRecorder = AudioRecorder();
  }

  @override
  void dispose() {
    _locationTimer?.cancel();
    _imeiController.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  // --- FUNÇÕES DE CÂMERA E FOTO ---
  Future<void> _tirarFoto() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera, imageQuality: 80);
    if (image != null) {
      setState(() {
        _selectedImage = File(image.path);
        _statusMessage = "Foto capturada com sucesso!";
      });
    }
  }

  Future<void> _escolherDaGaleria() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (image != null) {
      setState(() {
        _selectedImage = File(image.path);
        _statusMessage = "Imagem selecionada da galeria.";
      });
    }
  }

  // --- FUNÇÕES DE ÁUDIO ---
  Future<void> _iniciarGravacao() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        final Directory appDir = await getApplicationDocumentsDirectory();
        String filePath = '${appDir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';

        await _audioRecorder.start(const RecordConfig(), path: filePath);
        setState(() {
          _isRecording = true;
          _statusMessage = "Gravando áudio...";
        });
      }
    } catch (e) {
      print("Erro ao iniciar gravação: $e");
    }
  }

  Future<void> _pararGravacao() async {
    try {
      final path = await _audioRecorder.stop();
      setState(() {
        _isRecording = false;
        _audioPath = path;
        _statusMessage = "Áudio gravado com sucesso!";
      });
    } catch (e) {
      print("Erro ao parar gravação: $e");
    }
  }

  // --- CONTROLE DE RASTREIO ---
  void _toggleTracking() async {
    if (_isTracking) {
      _locationTimer?.cancel();
      setState(() {
        _isTracking = false;
        _statusMessage = "Rastreamento pausado.";
      });
    } else {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() => _statusMessage = "Erro: O GPS está desativado.");
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('imei', _imeiController.text.trim());

      setState(() {
        _isTracking = true;
        _statusMessage = "Rastreando ativamente...";
      });

      _sendLocation();
      _locationTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
        _sendLocation();
      });
    }
  }

  Future<void> _sendLocation() async {
    if (!_isTracking) return;
    try {
      Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
      final prefs = await SharedPreferences.getInstance();
      String imei = prefs.getString('imei') ?? 'Douglasgarcia';

      double lat = position.latitude;
      double lon = position.longitude;
      double speed = position.speed * 3.6;
      String dataHora = DateTime.now().toIso8601String();

      final url = Uri.parse(
        'https://zeusrastreio.onrender.com/api/posicoes?imei=$imei&lat=$lat&lon=$lon&speed=$speed&data_hora=$dataHora'
      );

      final response = await http.get(url);
      if (response.statusCode == 200) {
        print("Posição enviada!");
      }
    } catch (e) {
      print("Erro envio: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Zeus - Rastreio & Multimídia')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            TextField(
              controller: _imeiController,
              decoration: const InputDecoration(
                labelText: 'Identificador do Dispositivo (IMEI)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 15),
            Text(
              _statusMessage,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: _isTracking ? Colors.green : Colors.black87,
              ),
            ),
            const SizedBox(height: 20),
            
            // Botão de Rastreio Principal
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _isTracking ? Colors.red : Colors.green,
                minimumSize: const Size.fromHeight(50),
              ),
              onPressed: _toggleTracking,
              child: Text(_isTracking ? 'PARAR RASTREIO' : 'INICIAR RASTREIO',
                  style: const TextStyle(color: Colors.white, fontSize: 16)),
            ),
            const Divider(height: 40),

            // Seção de Câmera e Fotos
            const Text("Controle de Câmera e Imagem", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _tirarFoto,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text("Tirar Foto"),
                ),
                ElevatedButton.icon(
                  onPressed: _escolherDaGaleria,
                  icon: const Icon(Icons.photo_library),
                  label: const Text("Galeria"),
                ),
              ],
            ),
            const SizedBox(height: 15),
            if (_selectedImage != null)
              Container(
                height: 150,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  image: DecorationImage(image: FileImage(_selectedImage!), fit: BoxFit.cover),
                ),
              ),
            const Divider(height: 40),

            // Seção de Gravação de Áudio
            const Text("Gravação de Áudio", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: _isRecording ? Colors.orange : Colors.blue,
                minimumSize: const Size.fromHeight(45),
              ),
              onPressed: _isRecording ? _pararGravacao : _iniciarGravacao,
              icon: Icon(_isRecording ? Icons.stop : Icons.mic),
              label: Text(_isRecording ? "Parar Gravação" : "Gravar Áudio"),
            ),
            if (_audioPath != null)
              Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Text(
                  "Áudio salvo em:\n$_audioPath",
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ),
          ],
        ),
      ),
    );
  }
}