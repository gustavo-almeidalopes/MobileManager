import os
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QHBoxLayout, QFileDialog, QMessageBox
)
from term_utils import load_term_for

class BaseDeviceDialog(QDialog):
    def __init__(self, parent=None, device=None, device_type: str = ""):
        super().__init__(parent)
        self.device_type = device_type
        self.device = device
        self.setWindowTitle(device_type.capitalize())
        self.term_file_path = None  # Armazenar o caminho do arquivo do termo

        # Main layout: apenas o formulário
        main_layout = QFormLayout(self)
        self.term_button = QPushButton("Sem termo")
        self.term_button.setEnabled(False)
        self.select_term_button = QPushButton("Selecionar Termo")

        # Load initial term
        if device and device.modelo:
            self.update_term(device.modelo)
        else:
            self.term_button.setText("Sem termo")
            self.term_button.setEnabled(False)

        # Conectar botões
        self.term_button.clicked.connect(self.open_term_file)
        self.select_term_button.clicked.connect(self.select_term_file)

        self._build_fields(main_layout)

        # Adicionar botões de termo e salvar ao formulário
        main_layout.addRow("Termo:", self.term_button)
        main_layout.addRow("", self.select_term_button)
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        main_layout.addRow("", save_button)

    def _build_fields(self, layout: QFormLayout):
        raise NotImplementedError("Must implement _build_fields in subclass")

    def get_data(self) -> dict:
        raise NotImplementedError("Must implement get_data in subclass")

    def update_term(self, model_text):
        """Atualiza o botão de termo com base no modelo digitado."""
        if model_text:
            _, file_path = load_term_for(self.device_type, model_text)
            if file_path:
                self.term_button.setText(os.path.basename(file_path))
                self.term_button.setEnabled(True)
                self.term_file_path = file_path
            else:
                self.term_button.setText("Sem termo")
                self.term_button.setEnabled(False)
                self.term_file_path = None
        else:
            self.term_button.setText("Sem termo")
            self.term_button.setEnabled(False)
            self.term_file_path = None

    def select_term_file(self):
        """Abre um diálogo para selecionar um arquivo de termo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Termo", "",
            "Documentos (*.pdf *.docx);;Todos os arquivos (*)"
        )
        if file_path:
            self.term_file_path = file_path
            self.term_button.setText(os.path.basename(file_path))
            self.term_button.setEnabled(True)

    def open_term_file(self):
        """Abre o arquivo do termo no visualizador padrão."""
        if self.term_file_path:
            try:
                os.startfile(self.term_file_path)  # Windows
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo: {str(e)}")

class NotebookDialog(BaseDeviceDialog):
    def __init__(self, parent=None, notebook=None):
        super().__init__(parent, notebook, "notebook")

    def _build_fields(self, layout):
        self.fields = {
            'usuario': QLineEdit(self.device.usuario if self.device else ""),
            'matricula': QLineEdit(self.device.matricula if self.device else ""),
            'modelo': QLineEdit(self.device.modelo if self.device else ""),
            'numero_serie': QLineEdit(self.device.numero_serie if self.device else ""),
            'status': QComboBox(),
        }
        self.fields['status'].addItems(["Ativo", "Inativo", "Roubado/Furtado", "Em Conserto"])
        if self.device and self.device.status:
            self.fields['status'].setCurrentText(self.device.status)
        # Conectar o campo modelo à atualização do termo
        self.fields['modelo'].textChanged.connect(self.update_term)
        for label, widget in self.fields.items():
            layout.addRow(label.capitalize() + ':', widget)

    def get_data(self) -> dict:
        data = {k: w.text() if isinstance(w, QLineEdit) else w.currentText() for k, w in self.fields.items()}
        return data

class SimCardDialog(BaseDeviceDialog):
    def __init__(self, parent=None, sim=None):
        super().__init__(parent, sim, "simcard")

    def _build_fields(self, layout):
        self.fields = {
            'iccid': QLineEdit(self.device.iccid if self.device else ""),
            'operadora': QLineEdit(self.device.operadora if self.device else ""),
            'status': QComboBox(),
        }
        self.fields['status'].addItems(["Ativo", "Bloqueado", "Roubado/Furtado"])
        if self.device and self.device.status:
            self.fields['status'].setCurrentText(self.device.status)
        for label, widget in self.fields.items():
            layout.addRow(label.capitalize() + ':', widget)

    def get_data(self) -> dict:
        data = {k: w.text() if isinstance(w, QLineEdit) else w.currentText() for k, w in self.fields.items()}
        return data

class MobileDialog(BaseDeviceDialog):
    def __init__(self, parent=None, mobile=None):
        super().__init__(parent, mobile, "mobile")

    def _build_fields(self, layout):
        self.fields = {
            'usuario': QLineEdit(self.device.usuario if self.device else ""),
            'matricula': QLineEdit(self.device.matricula if self.device else ""),
            'modelo': QLineEdit(self.device.modelo if self.device else ""),
            'imei1': QLineEdit(self.device.imei1 if self.device else ""),
            'imei2': QLineEdit(self.device.imei2 if self.device else ""),
            'chip_em_uso': QLineEdit(self.device.chip_em_uso if self.device else ""),
            'numero_serie': QLineEdit(self.device.numero_serie if self.device else ""),
            'status': QComboBox(),
        }
        self.fields['status'].addItems(["Ativo", "Inativo", "Roubado/Furtado", "Em Conserto"])
        if self.device and self.device.status:
            self.fields['status'].setCurrentText(self.device.status)
        # Conectar o campo modelo à atualização do termo
        self.fields['modelo'].textChanged.connect(self.update_term)
        for label, widget in self.fields.items():
            layout.addRow(label.capitalize() + ':', widget)

    def get_data(self) -> dict:
        data = {k: w.text() if isinstance(w, QLineEdit) else w.currentText() for k, w in self.fields.items()}
        return data
