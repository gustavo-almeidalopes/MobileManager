from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, QMessageBox
from database import Session, Notebook, Log
from dialogs import NotebookDialog

class NotebookTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.current_user = "admin"
        self._build_ui()
        self.apply_filters()

    def _build_ui(self):
        layout = QVBoxLayout()
        filter_layout = QFormLayout()
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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Status", "Usuário", "Matrícula", "Modelo", "Serial"])
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
        q = self.session.query(Notebook)
        status = self.status_filter.currentText()
        if status != "Todos": q = q.filter(Notebook.status == status)
        model = self.model_filter.text()
        if model: q = q.filter(Notebook.modelo.like(f"%{model}%"))
        res = q.all()
        self._update_table(res)

    def _update_table(self, res):
        self.table.setRowCount(len(res))
        for i, nb in enumerate(res):
            self.table.setItem(i, 0, QTableWidgetItem(str(nb.id)))
            self.table.setItem(i, 1, QTableWidgetItem(nb.status or ""))
            self.table.setItem(i, 2, QTableWidgetItem(nb.usuario or ""))
            self.table.setItem(i, 3, QTableWidgetItem(nb.matricula or ""))
            self.table.setItem(i, 4, QTableWidgetItem(nb.modelo or ""))
            self.table.setItem(i, 5, QTableWidgetItem(nb.numero_serie or ""))
        self.result_count.setText(f"Resultados: {len(res)}")

    def add(self):
        dlg = NotebookDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            new = Notebook(**data)
            self.session.add(new)
            self.session.commit()
            self.log("adicionar", new.id)
            self.apply_filters()

    def edit(self):
        idx = self.table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um notebook para editar.")
            return
        nid = int(self.table.item(idx, 0).text())
        nb = self.session.query(Notebook).get(nid)
        dlg = NotebookDialog(self, nb)
        if dlg.exec_():
            for k,v in dlg.get_data().items(): setattr(nb, k, v)
            self.session.commit()
            self.log("editar", nb.id)
            self.apply_filters()

    def delete(self):
        idx = self.table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um notebook para excluir.")
            return
        nid = int(self.table.item(idx, 0).text())
        if QMessageBox.question(self, "Confirmação", "Tem certeza?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            nb = self.session.query(Notebook).get(nid)
            self.session.delete(nb)
            self.session.commit()
            self.log("excluir", nid)
            self.apply_filters()

    def log(self, action, detail):
        entry = Log(usuario=self.current_user, acao=action, detalhes=str(detail))
        self.session.add(entry); self.session.commit()
