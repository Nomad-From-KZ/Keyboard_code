import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QListWidget, QListWidgetItem,
    QTextEdit, QGroupBox, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QFileDialog
)

from models import AppConfig, CodeBlock
from config_manager import ConfigManager
from block_manager import BlockManager
from hotkey_manager import HotkeyManager
from keyboard_simulator import KeyboardSimulator
from keyboard_hook import KeyboardHook


class CodeControllerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Block Controller - Typing Layer")
        self.resize(750, 650)

        # Менеджеры и сервисы
        self.config_manager = ConfigManager()
        self.config: AppConfig = self.config_manager.load_config()

        self.block_manager = BlockManager(self.config.blocks)
        self.hotkey_manager = HotkeyManager(self.config.hotkeys)
        self.simulator = KeyboardSimulator(self.config.delay_ms, self.config.tab_mode)

        self.hook = KeyboardHook(self.hotkey_manager)
        self.hook.signals.action_triggered.connect(self.on_action_triggered)
        self.hook.signals.type_trigger.connect(self.on_type_trigger)
        self.hook.signals.backspace_trigger.connect(self.on_backspace_trigger)

        self.is_paused = False

        self.init_ui()
        self.refresh_ui_state()

        if not self.hook.start():
            QMessageBox.critical(self, "Error", "Failed to install global Win32 keyboard hook!")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Панель управления
        dash_group = QGroupBox("Live Control Dashboard")
        dash_layout = QVBoxLayout(dash_group)

        status_hlayout = QHBoxLayout()
        self.lbl_status = QLabel("Status: ACTIVE")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        self.lbl_block = QLabel("Current Block: None")
        self.lbl_block.setStyleSheet("font-size: 13px;")

        status_hlayout.addWidget(self.lbl_status)
        status_hlayout.addStretch()
        status_hlayout.addWidget(self.lbl_block)
        dash_layout.addLayout(status_hlayout)

        progress_hlayout = QHBoxLayout()
        self.lbl_position = QLabel("Position: 0 / 0")
        self.lbl_progress = QLabel("Progress: 0.0%")
        self.lbl_next_char = QLabel("Next: [ EOF ]")
        self.lbl_next_char.setStyleSheet("font-weight: bold; font-size: 15px; color: #0055ff;")

        progress_hlayout.addWidget(self.lbl_position)
        progress_hlayout.addWidget(self.lbl_progress)
        progress_hlayout.addStretch()
        progress_hlayout.addWidget(self.lbl_next_char)
        dash_layout.addLayout(progress_hlayout)

        ctrl_hlayout = QHBoxLayout()
        ctrl_hlayout.addWidget(QLabel("Delay (ms):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 1000)
        self.spin_delay.setValue(self.config.delay_ms)
        self.spin_delay.valueChanged.connect(self.on_delay_changed)
        ctrl_hlayout.addWidget(self.spin_delay)

        ctrl_hlayout.addWidget(QLabel("Tab Mode:"))
        self.combo_tab = QComboBox()
        self.combo_tab.addItems(["4_spaces", "2_spaces", "tab"])
        self.combo_tab.setCurrentText(self.config.tab_mode)
        self.combo_tab.currentTextChanged.connect(self.on_tab_mode_changed)
        ctrl_hlayout.addWidget(self.combo_tab)

        ctrl_hlayout.addStretch()

        self.btn_pause = QPushButton("Pause (F8)")
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_reset = QPushButton("Reset Position (Ctrl+R)")
        self.btn_reset.clicked.connect(self.reset_current_block)

        ctrl_hlayout.addWidget(self.btn_pause)
        ctrl_hlayout.addWidget(self.btn_reset)
        dash_layout.addLayout(ctrl_hlayout)

        main_layout.addWidget(dash_group)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_blocks_tab(), "Code Blocks")
        self.tabs.addTab(self.create_hotkeys_tab(), "Hotkey Configuration")
        main_layout.addWidget(self.tabs)

    def create_blocks_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("Available Code Blocks:"))
        self.list_blocks = QListWidget()
        self.list_blocks.currentRowChanged.connect(self.on_block_selection_changed)
        left_box.addWidget(self.list_blocks)

        btn_box = QHBoxLayout()
        btn_add = QPushButton("Add Block")
        btn_add.clicked.connect(self.add_new_block)
        
        btn_import = QPushButton("Import Folder")
        btn_import.clicked.connect(self.import_blocks_from_folder)

        btn_del = QPushButton("Delete Block")
        btn_del.clicked.connect(self.delete_block)

        btn_box.addWidget(btn_add)
        btn_box.addWidget(btn_import)
        btn_box.addWidget(btn_del)
        left_box.addLayout(btn_box)

        layout.addLayout(left_box, 1)

        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("Block ID:"))
        self.edit_block_id = QLineEdit()
        right_box.addWidget(self.edit_block_id)

        right_box.addWidget(QLabel("Block Display Name:"))
        self.edit_block_name = QLineEdit()
        right_box.addWidget(self.edit_block_name)

        right_box.addWidget(QLabel("Source Code:"))
        self.txt_block_code = QTextEdit()
        right_box.addWidget(self.txt_block_code)

        btn_save_block = QPushButton("Save Block Changes")
        btn_save_block.clicked.connect(self.save_block_changes)
        right_box.addWidget(btn_save_block)

        layout.addLayout(right_box, 2)
        return widget

    def create_hotkeys_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Hotkey Map Settings (Hotkey -> Action/Block ID):"))

        self.table_hotkeys = QTableWidget()
        self.table_hotkeys.setColumnCount(2)
        self.table_hotkeys.setHorizontalHeaderLabels(["Hotkey Combo", "Action / Target Block ID"])
        self.table_hotkeys.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_hotkeys)

        btn_layout = QHBoxLayout()
        btn_add_hk = QPushButton("Add Row")
        btn_add_hk.clicked.connect(self.add_hotkey_row)

        btn_gen_hk = QPushButton("Generate Hotkeys for All Blocks")
        btn_gen_hk.clicked.connect(self.generate_hotkeys_for_all_blocks)

        btn_del_hk = QPushButton("Delete Row")
        btn_del_hk.clicked.connect(self.delete_hotkey_row)

        btn_save_hk = QPushButton("Apply & Save Hotkeys")
        btn_save_hk.clicked.connect(self.save_hotkey_table)

        btn_layout.addWidget(btn_add_hk)
        btn_layout.addWidget(btn_gen_hk)
        btn_layout.addWidget(btn_del_hk)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save_hk)
        layout.addLayout(btn_layout)

        return widget

    def refresh_ui_state(self):
        active_block = self.block_manager.get_active_block()
        if active_block:
            self.lbl_block.setText(f"Current Block: {active_block.name} [{active_block.id}]")
            pos = active_block.position
            total = len(active_block.code)
            pct = (pos / total * 100) if total > 0 else 0.0

            self.lbl_position.setText(f"Position: {pos} / {total}")
            self.lbl_progress.setText(f"Progress: {pct:.1f}%")

            next_c = active_block.get_next_char()
            if next_c is None:
                self.lbl_next_char.setText("Next: [ EOF ]")
            elif next_c == "\n":
                self.lbl_next_char.setText("Next: [ Enter \\n ]")
            elif next_c == "\t":
                self.lbl_next_char.setText("Next: [ Tab \\t ]")
            elif next_c == " ":
                self.lbl_next_char.setText("Next: [ Space ]")
            else:
                self.lbl_next_char.setText(f"Next: {next_c}")
        else:
            self.lbl_block.setText("Current Block: None")
            self.lbl_position.setText("Position: 0 / 0")
            self.lbl_progress.setText("Progress: 0.0%")
            self.lbl_next_char.setText("Next: N/A")

        self.list_blocks.blockSignals(True)
        self.list_blocks.clear()
        for b in self.config.blocks:
            item = QListWidgetItem(f"{b.name} ({b.id})")
            item.setData(Qt.ItemDataRole.UserRole, b.id)
            self.list_blocks.addItem(item)
            if self.block_manager.active_block_id == b.id:
                self.list_blocks.setCurrentItem(item)
        self.list_blocks.blockSignals(False)

        self.table_hotkeys.setRowCount(0)
        for i, (combo, act) in enumerate(self.config.hotkeys.items()):
            self.table_hotkeys.insertRow(i)
            # Если хоткей был временным пустым ключом — показываем пустую строку
            display_combo = "" if combo.startswith("__EMPTY_KEY_") else combo
            self.table_hotkeys.setItem(i, 0, QTableWidgetItem(display_combo))
            self.table_hotkeys.setItem(i, 1, QTableWidgetItem(act))

    def on_action_triggered(self, action: str):
        if action == "toggle_pause":
            self.toggle_pause()
            return

        if self.is_paused:
            return

        if action == "reset_block":
            self.reset_current_block()
        elif action.startswith("block_") or action in self.block_manager.blocks:
            if self.block_manager.select_block(action):
                self.refresh_ui_state()

    def on_type_trigger(self):
        if self.is_paused:
            return

        active_block = self.block_manager.get_active_block()
        if not active_block:
            return

        char_to_type = active_block.get_next_char()
        if char_to_type is not None:
            self.simulator.type_char(char_to_type)
            self.block_manager.advance_current_block()
            self.refresh_ui_state()

    def on_backspace_trigger(self):
        if self.is_paused:
            return

        self.simulator.send_backspace()
        self.block_manager.rewind_current_block()
        self.refresh_ui_state()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.hook.is_paused = self.is_paused

        if self.is_paused:
            self.lbl_status.setText("Status: PAUSED")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
            self.btn_pause.setText("Resume (F8)")
        else:
            self.lbl_status.setText("Status: ACTIVE")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
            self.btn_pause.setText("Pause (F8)")

    def reset_current_block(self):
        self.block_manager.reset_current_block()
        self.refresh_ui_state()

    def on_delay_changed(self, val: int):
        self.config.delay_ms = val
        self.simulator.set_delay(val)
        self.config_manager.save_config(self.config)

    def on_tab_mode_changed(self, mode: str):
        self.config.tab_mode = mode
        self.simulator.set_tab_mode(mode)
        self.config_manager.save_config(self.config)

    def on_block_selection_changed(self, row: int):
        if row < 0:
            return
        item = self.list_blocks.item(row)
        b_id = item.data(Qt.ItemDataRole.UserRole)
        if b_id in self.block_manager.blocks:
            b = self.block_manager.blocks[b_id]
            self.edit_block_id.setText(b.id)
            self.edit_block_name.setText(b.name)
            self.txt_block_code.setText(b.code)

    def add_new_block(self):
        new_id = f"block_{len(self.config.blocks) + 1}"
        new_b = CodeBlock(id=new_id, name=f"New Block {new_id}", code="// Write code here\n")
        self.config.blocks.append(new_b)
        self.block_manager.set_blocks(self.config.blocks)
        self.config_manager.save_config(self.config)
        self.refresh_ui_state()

    def import_blocks_from_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с файлами")
        if not folder:
            return

        supported_ext = ('.py', '.cpp', '.hpp', '.c', '.h', '.js', '.ts', '.java', '.cs', '.txt')
        files = [f for f in os.listdir(folder) if f.endswith(supported_ext)]

        if not files:
            QMessageBox.information(self, "Инфо", "В выбранной папке нет подходящих файлов.")
            return

        start_idx = len(self.config.blocks) + 1

        for idx, file_name in enumerate(sorted(files), start=start_idx):
            file_path = os.path.join(folder, file_name)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            block_id = f"block_{idx}"
            block_name = os.path.splitext(file_name)[0]

            new_block = CodeBlock(id=block_id, name=block_name, code=content)
            self.config.blocks.append(new_block)

        self.block_manager.set_blocks(self.config.blocks)
        self.config_manager.save_config(self.config)
        self.refresh_ui_state()

        QMessageBox.information(self, "Успех", f"Успешно импортировано файлов: {len(files)}!")

    def delete_block(self):
        curr_row = self.list_blocks.currentRow()
        if curr_row < 0:
            return
        item = self.list_blocks.item(curr_row)
        b_id = item.data(Qt.ItemDataRole.UserRole)

        self.config.blocks = [b for b in self.config.blocks if b.id != b_id]
        self.block_manager.set_blocks(self.config.blocks)
        self.config_manager.save_config(self.config)
        self.refresh_ui_state()

    def save_block_changes(self):
        curr_row = self.list_blocks.currentRow()
        if curr_row < 0:
            return

        item = self.list_blocks.item(curr_row)
        old_id = item.data(Qt.ItemDataRole.UserRole)

        for b in self.config.blocks:
            if b.id == old_id:
                b.id = self.edit_block_id.text().strip()
                b.name = self.edit_block_name.text().strip()
                b.code = self.txt_block_code.toPlainText()

        self.block_manager.set_blocks(self.config.blocks)
        self.config_manager.save_config(self.config)
        self.refresh_ui_state()
        QMessageBox.information(self, "Success", "Block updated successfully!")

    # --- Управление таблицей хоткеев ---
    def add_hotkey_row(self):
        row = self.table_hotkeys.rowCount()
        self.table_hotkeys.insertRow(row)
        self.table_hotkeys.setItem(row, 0, QTableWidgetItem(""))
        self.table_hotkeys.setItem(row, 1, QTableWidgetItem("block_1"))

    def generate_hotkeys_for_all_blocks(self):
        existing_actions = set(self.config.hotkeys.values())
        added_count = 0

        for block in self.config.blocks:
            if block.id not in existing_actions:
                # Генерируем уникальный временный ключ для каждого блока
                unique_empty_key = f"__EMPTY_KEY_{block.id}"
                self.config.hotkeys[unique_empty_key] = block.id
                existing_actions.add(block.id)
                added_count += 1

        if added_count > 0:
            self.hotkey_manager.update_map(self.config.hotkeys)
            self.config_manager.save_config(self.config)
            self.refresh_ui_state()
            QMessageBox.information(
                self, 
                "Успех", 
                f"Добавлено {added_count} блоков в таблицу хоткеев!\nТеперь вы можете проставить нужные клавиши вручную."
            )
        else:
            QMessageBox.information(self, "Инфо", "Все блоки уже добавлены в таблицу хоткеев.")

    def delete_hotkey_row(self):
        row = self.table_hotkeys.currentRow()
        if row >= 0:
            self.table_hotkeys.removeRow(row)

    def save_hotkey_table(self):
        new_map = {}
        for row in range(self.table_hotkeys.rowCount()):
            hk_item = self.table_hotkeys.item(row, 0)
            act_item = self.table_hotkeys.item(row, 1)
            
            if act_item:
                act = act_item.text().strip()
                hk = hk_item.text().strip() if hk_item else ""
                
                # Сохраняем строку, если указано действие/блок
                if act:
                    # Если клавиша не введена, сохраняем уникальный служебный ключ
                    key_to_save = hk if hk else f"__EMPTY_KEY_{act}"
                    new_map[key_to_save] = act

        self.config.hotkeys = new_map
        self.hotkey_manager.update_map(new_map)
        self.config_manager.save_config(self.config)
        QMessageBox.information(self, "Success", "Hotkey configuration applied!")

    def closeEvent(self, event):
        self.hook.stop()
        event.accept()