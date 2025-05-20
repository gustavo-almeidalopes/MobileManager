from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, QMessageBox
)
from database import Session, Mobile, Log
from dialogs import MobileDialog

class MobileTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.current_user = "admin"
        self._build_ui()
        self.apply_filters()

    def _build_ui(self):
        layout = QVBoxLayout()
        filter_layout = QFormLayout()
        # status and model filters
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Ativos", "Inativos", "Roubados/Furtados", "Em Conserto"])
        self.model_filter = QLineEdit()
        filter_layout.addRow("Status:", self.status_filter)
        filter_layout.addRow("Modelo:", self.model_filter)
        layout.addLayout(filter_layout)

        btn_apply = QPushButton("Aplicar Filtros")
        btn_apply.clicked.connect(self.apply_filters)
        layout.addWidget(btn_apply)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Status", "Usuário", "Matrícula", "Linha", "Modelo",
            "IMEI1", "IMEI2", "Chip", "Serial"
        ])
        layout.addWidget(self.table)

        self.result_count = QLabel()
        layout.addWidget(self.result_count)

        btn_layout = QHBoxLayout()
        for name, handler in [("Adicionar", self.add), ("Editar", self.edit), ("Excluir", self.delete)]:
            btn = QPushButton(name)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def apply_filters(self):
        q = self.session.query(Mobile)
        status = self.status_filter.currentText()
        if status != "Todos":
            q = q.filter(Mobile.status == status)
        model = self.model_filter.text()
        if model:
            q = q.filter(Mobile.modelo.like(f"%{model}%"))
        results = q.all()
        self._update_table(results)

    def _update_table(self, results):
        self.table.setRowCount(len(results))
        for i, m in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(str(m.id)))
            self.table.setItem(i, 1, QTableWidgetItem(m.status or ""))
            self.table.setItem(i, 2, QTableWidgetItem(m.usuario or ""))
            self.table.setItem(i, 3, QTableWidgetItem(m.matricula or ""))
            self.table.setItem(i, 4, QTableWidgetItem(m.msisdn or ""))
            self.table.setItem(i, 5, QTableWidgetItem(m.modelo or ""))
            self.table.setItem(i, 6, QTableWidgetItem(m.imei1 or ""))
            self.table.setItem(i, 7, QTableWidgetItem(m.imei2 or ""))
            self.table.setItem(i, 8, QTableWidgetItem(m.chip_em_uso or ""))
            self.table.setItem(i, 9, QTableWidgetItem(m.numero_serie or ""))
        self.result_count.setText(f"Resultados: {len(results)}")

    def add(self):
        dlg = MobileDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            new = Mobile(**data)
            self.session.add(new)
            self.session.commit()
            self.log("adicionar", new.id)
            self.apply_filters()

    def edit(self):
        idx = self.table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um celular para editar.")
            return
        mid = int(self.table.item(idx, 0).text())
        m = self.session.query(Mobile).get(mid)
        dlg = MobileDialog(self, m)
        if dlg.exec_():
            for k, v in dlg.get_data().items(): setattr(m, k, v)
            self.session.commit()
            self.log("editar", m.id)
            self.apply_filters()

    def delete(self):
        idx = self.table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um celular para excluir.")
            return
        mid = int(self.table.item(idx, 0).text())
        confirm = QMessageBox.question(self, "Confirmação", "Tem certeza?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            m = self.session.query(Mobile).get(mid)
            self.session.delete(m)
            self.session.commit()
            self.log("excluir", mid)
            self.apply_filters()

    def log(self, action, detail):
        entry = Log(usuario=self.current_user, acao=action, detalhes=str(detail))
        self.session.add(entry)
        self.session.commit()
