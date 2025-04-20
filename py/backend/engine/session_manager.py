import os


class SessionManager:
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir

    def list_sessions(self) -> dict[str, tuple[str, str]]:
        """List all sessions in the memory directory.
        
        Returns:
            A dictionary mapping session IDs to tuples of (name, filename)
        """
        sessions = {}
        files = os.listdir(self.memory_dir)
        for f in files:
            if f.endswith('.json'):
                try:
                    # Parse the filename, which should be in the format "session_id~title.json"
                    parts = os.path.basename(f).split('~', 1)
                    if len(parts) != 2:
                        continue  # Skip files that don't follow the expected format
                    
                    session_id = parts[0]
                    name_with_ext = parts[1]
                    name = name_with_ext.rsplit('.json', 1)[0]  # Remove .json extension
                    
                    # Store session info as (name, full_filename)
                    full_path = os.path.join(self.memory_dir, f)
                    sessions[session_id] = (name, full_path)
                except Exception:
                    # Skip any files that cause parsing errors
                    continue
                    
        return sessions

    def delete_session(self, session_id: str):
        """Delete a session by its ID."""
        sessions = self.list_sessions()
        if session_id not in sessions:
            raise RuntimeError(f"Session {session_id} not found.")

        filename = sessions[session_id][1]
        os.remove(filename)