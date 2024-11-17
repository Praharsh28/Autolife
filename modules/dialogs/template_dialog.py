from PyQt5.QtWidgets import (QListWidget, QTextEdit, QLabel, QFileDialog,
                             QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
                             QGroupBox, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt
import json
import os
from .base_dialog import BaseDialog

class TemplateManagementDialog(BaseDialog):
    """Dialog for managing processing templates."""
    
    description = """Create, edit, and manage templates for common processing tasks.
                    Save your frequently used settings for quick access."""
    
    def __init__(self, parent=None):
        self.templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        super().__init__("Template Management", parent)
        self.setup_ui()
        self.load_templates()
        
    def setup_ui(self):
        # Template list
        templates_group = QGroupBox("Templates")
        templates_layout = QVBoxLayout()
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._template_selected)
        templates_layout.addWidget(self.template_list)
        
        # Template buttons
        button_layout = QHBoxLayout()
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._new_template)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_template)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_template)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._export_template)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self._import_template)
        
        button_layout.addWidget(new_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(import_btn)
        templates_layout.addLayout(button_layout)
        
        templates_group.setLayout(templates_layout)
        self.content_layout.addWidget(templates_group)
        
        # Template details
        details_group = QGroupBox("Template Details")
        details_layout = QVBoxLayout()
        
        # Template name
        name_layout = QHBoxLayout()
        self.template_name = QLineEdit()
        self.template_name.setPlaceholderText("Enter template name...")
        
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addWidget(self.template_name)
        details_layout.addLayout(name_layout)
        
        # Template category
        category_layout = QHBoxLayout()
        self.template_category = QComboBox()
        self.template_category.addItems([
            "Subtitle Generation",
            "Format Conversion",
            "Subtitle Editing",
            "Batch Processing",
            "Other"
        ])
        
        category_layout.addWidget(QLabel("Category:"))
        category_layout.addWidget(self.template_category)
        category_layout.addStretch()
        details_layout.addLayout(category_layout)
        
        # Template description
        self.template_description = QTextEdit()
        self.template_description.setPlaceholderText("Enter template description...")
        details_layout.addWidget(QLabel("Description:"))
        details_layout.addWidget(self.template_description)
        
        # Template settings
        self.template_settings = QTextEdit()
        self.template_settings.setPlaceholderText("Enter template settings in JSON format...")
        details_layout.addWidget(QLabel("Settings:"))
        details_layout.addWidget(self.template_settings)
        
        details_group.setLayout(details_layout)
        self.content_layout.addWidget(details_group)
        
    def load_templates(self):
        """Load all templates from the templates directory."""
        self.template_list.clear()
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                self.template_list.addItem(filename[:-5])  # Remove .json extension
                
    def _template_selected(self, current, previous):
        """Handle template selection."""
        if current:
            template_path = os.path.join(self.templates_dir, f"{current.text()}.json")
            try:
                with open(template_path, 'r') as f:
                    template = json.load(f)
                    
                self.template_name.setText(template.get('name', ''))
                self.template_category.setCurrentText(template.get('category', ''))
                self.template_description.setText(template.get('description', ''))
                self.template_settings.setText(
                    json.dumps(template.get('settings', {}), indent=2)
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load template: {str(e)}"
                )
                
    def _new_template(self):
        """Create a new template."""
        self.template_list.clearSelection()
        self.template_name.clear()
        self.template_description.clear()
        self.template_settings.clear()
        
    def _save_template(self):
        """Save the current template."""
        name = self.template_name.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Error",
                "Please enter a template name."
            )
            return
            
        try:
            settings = json.loads(self.template_settings.toPlainText())
        except json.JSONDecodeError:
            QMessageBox.warning(
                self,
                "Error",
                "Invalid JSON in settings field."
            )
            return
            
        template = {
            'name': name,
            'category': self.template_category.currentText(),
            'description': self.template_description.toPlainText(),
            'settings': settings
        }
        
        template_path = os.path.join(self.templates_dir, f"{name}.json")
        try:
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            self.load_templates()
            QMessageBox.information(
                self,
                "Success",
                "Template saved successfully."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save template: {str(e)}"
            )
            
    def _delete_template(self):
        """Delete the selected template."""
        current = self.template_list.currentItem()
        if not current:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{current.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            template_path = os.path.join(self.templates_dir, f"{current.text()}.json")
            try:
                os.remove(template_path)
                self.load_templates()
                self._new_template()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete template: {str(e)}"
                )
                
    def _export_template(self):
        """Export the selected template."""
        current = self.template_list.currentItem()
        if not current:
            return
            
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Template",
            f"{current.text()}.json",
            "JSON Files (*.json)"
        )
        
        if export_path:
            template_path = os.path.join(self.templates_dir, f"{current.text()}.json")
            try:
                with open(template_path, 'r') as src, open(export_path, 'w') as dst:
                    dst.write(src.read())
                    
                QMessageBox.information(
                    self,
                    "Success",
                    "Template exported successfully."
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to export template: {str(e)}"
                )
                
    def _import_template(self):
        """Import a template."""
        import_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Template",
            "",
            "JSON Files (*.json)"
        )
        
        if import_path:
            try:
                with open(import_path, 'r') as f:
                    template = json.load(f)
                    
                if not all(k in template for k in ['name', 'category', 'description', 'settings']):
                    raise ValueError("Invalid template format")
                    
                template_path = os.path.join(self.templates_dir, f"{template['name']}.json")
                with open(template_path, 'w') as f:
                    json.dump(template, f, indent=2)
                    
                self.load_templates()
                QMessageBox.information(
                    self,
                    "Success",
                    "Template imported successfully."
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to import template: {str(e)}"
                )
                
    def get_values(self):
        """Get the dialog values as a dictionary."""
        try:
            settings = json.loads(self.template_settings.toPlainText())
        except json.JSONDecodeError:
            settings = {}
            
        return {
            'name': self.template_name.text(),
            'category': self.template_category.currentText(),
            'description': self.template_description.toPlainText(),
            'settings': settings
        }
