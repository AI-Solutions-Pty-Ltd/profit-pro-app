    function buildLabels(visibleRows) {
        labelEl.innerHTML = '';
        visibleRows.forEach((row, i) => {
            const div = document.createElement('div');
            div.style.height = ROW_H + 'px';
            div.className = `flex items-center px-4 border-b border-gray-50 text-[11px] transition-all cursor-pointer group/label ${row.has_children ? 'font-bold text-gray-900 bg-gray-50/20' : 'text-gray-600'}`;
            if (i % 2 === 1) div.style.backgroundColor = 'rgba(250, 250, 250, 0.5)';
            if (row.id === highlightTaskId) div.classList.add('bg-indigo-50/50');
            
            // Toggle row state on click
            div.onclick = (e) => {
                if (row.has_children) {
                    if (collapsedState.has(row.id)) collapsedState.delete(row.id);
                    else collapsedState.add(row.id);
                    render();
                } else if (window.scrollToTask) {
                    window.scrollToTask(row.id);
                }
            };

            // Hierarchy Lines Container
            const indentWrapper = document.createElement('div');
            indentWrapper.className = 'flex items-center h-full mr-2';
            for (let d = 0; d < row.depth; d++) {
                const line = document.createElement('div');
                line.className = 'w-4 h-full border-l border-gray-200/60 ml-2 first:ml-0';
                indentWrapper.appendChild(line);
            }
            div.appendChild(indentWrapper);

            // Chevron/State Indicator
            if (row.has_children) {
                const isCollapsed = collapsedState.has(row.id);
                const chevron = document.createElement('span');
                chevron.className = `mr-2 flex items-center justify-center w-5 h-5 rounded transition-all ${isCollapsed ? 'bg-indigo-50 text-indigo-600' : 'text-gray-400 group-hover/label:text-indigo-500'}`;
                chevron.innerHTML = `<svg class="w-3.5 h-3.5 transform transition-transform ${isCollapsed ? '-rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path></svg>`;
                div.appendChild(chevron);
            } else {
                const dot = document.createElement('div');
                dot.className = 'w-1.5 h-1.5 bg-gray-300 rounded-full mr-3 ml-2 group-hover/label:bg-indigo-400 transition-colors';
                div.appendChild(dot);
            }

            const textContainer = document.createElement('div');
            textContainer.className = 'flex items-center flex-1 min-w-0';
            
            const text = document.createElement('span');
            text.className = 'truncate';
            text.textContent = row.activity;
            textContainer.appendChild(text);

            // Collapsed Count Indicator
            if (row.has_children && collapsedState.has(row.id)) {
                let count = 0;
                let found = false;
                for(let r of GANTT_DATA) {
                    if (found) {
                        if (r.depth <= row.depth) break;
                        if (r.parent_id === row.id) count++; 
                    }
                    if (r.id === row.id) found = true;
                }
                
                if (count > 0) {
                    const badge = document.createElement('span');
                    badge.className = 'ml-2 px-1.5 py-0.5 bg-gray-100 text-[9px] font-bold text-gray-500 rounded-md border border-gray-200';
                    badge.textContent = `+${count}`;
                    textContainer.appendChild(badge);
                }
            }
            
            div.appendChild(textContainer);
            labelEl.appendChild(div);
        });
    }
