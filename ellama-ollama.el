;;; ellama-ollama.el --- Ellama integration with Ollama

;;; Commentary:
;; This package provides integration between Ellama and Ollama

;;; Code:

(require 'json)

(defun ellama-ollama-get-models ()
  "Retrieve and display the list of available Ollama models."
  (interactive)
  (let ((models (ellama-ollama--run-python-script "get_models")))
    (with-current-buffer (get-buffer-create "*Ollama Models*")
      (erase-buffer)
      (insert "Available Ollama Models:\n\n")
      (if models
          (dolist (model models)
            (insert (format "- %s\n" model)))
        (insert "No models found or unable to retrieve models."))
      (goto-char (point-min))
      (display-buffer (current-buffer)))))

(defun ellama-ollama-get-help (model-name query)
  "Get help for a specific MODEL-NAME using QUERY."
  (interactive "sEnter model name: \nsEnter query: ")
  (let ((help-text (ellama-ollama--run-python-script (format "get_help %s %s" model-name query))))
    (with-current-buffer (get-buffer-create "*Ollama Help*")
      (erase-buffer)
      (insert (format "Help for %s:\n\n" model-name))
      (insert (or (cdr (assoc 'help help-text)) "No help available."))
      (goto-char (point-min))
      (display-buffer (current-buffer)))))

(defun ellama-ollama--run-python-script (args)
  "Run Python script with ARGS and return the result."
  (with-temp-buffer
    (call-process "python" nil t nil
                  "ollama_helper.py"
                  args)
    (goto-char (point-min))
    (ignore-errors
      (json-read-from-string (buffer-string)))))

(defun ellama-ollama-insert-help-at-point (model-name query)
  "Insert help for MODEL-NAME using QUERY at the current point in the buffer."
  (interactive "sEnter model name: \nsEnter query: ")
  (let ((help-text (ellama-ollama--run-python-script (format "get_help %s %s" model-name query))))
    (insert (or (cdr (assoc 'help help-text)) "No help available."))))

(provide 'ellama-ollama)

;;; ellama-ollama.el ends here
