function escapeLabel(label) {
    return label.replace(/[&<>'"]/g, function(char) {
        switch (char) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case "'": return '&#39;';
            case '"': return '&quot;';
            default: return char;
        }
    });
}

$(document).ready(function() {
    // Initialize clipboard.js
    new ClipboardJS('.copy-icon');

    // Load nodes
    $.get('/get_nodes', function(nodes) {
        var select = $('#node-select');
        nodes.forEach(function(node) {
            select.append($('<option></option>').val(node).text(node));
        });
    });
    
    // Query node
    $('#query-node-btn').click(function() {
        var nodeName = $('#node-select').val();
        
        if (!nodeName) {
            alert('Please select a node.');
            return;
        }
        
        $.ajax({
            url: '/enrich_node',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                node_name: nodeName
            }),
            success: function(response) {
                $('#node-info').text(response.original_info);
            },
            error: function(xhr, status, error) {
                $('#node-info').text('Error: ' + error);
            }
        });
    });

    // Enrich node
    $('#enrich-node-btn').click(function() {
        var nodeName = $('#node-select').val();
        
        if (!nodeName) {
            alert('Please select a node.');
            return;
        }
        
        $.ajax({
            url: '/enrich_node',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                node_name: nodeName
            }),
            success: function(response) {
                $('#node-info').text('Original Info:\n' + response.original_info + '\n\nEnriched Info:\n' + response.enriched_info);
            },
            error: function(xhr, status, error) {
                $('#node-info').text('Error: ' + error);
            }
        });
    });

    // Export JSON
    $('#export-json-btn').click(function() {
        window.location.href = '/export_json';
    });

    // Load and render graph
    function loadAndRenderGraph() {
        $.get('/graph_data', function(data) {
            var nodes = data.nodes;
            var links = data.links;
            var mermaidCode = 'graph TD\n';

            links.forEach(function(link) {
                mermaidCode += `    ${escapeLabel(link.source)}["${escapeLabel(nodes.find(n => n.id === link.source).label || link.source)}"] -->|${escapeLabel(link.relation)}| ${escapeLabel(link.target)}["${escapeLabel(nodes.find(n => n.id === link.target).label || link.target)}"]\n`;
            });

            var mermaidDiv = document.getElementById('mermaid-graph');
            mermaidDiv.innerHTML = mermaidCode;
            mermaid.init(undefined, mermaidDiv);
        });
    }

    // Initial graph load
    loadAndRenderGraph();
});
