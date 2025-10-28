import json
import os
import sqlite3
from typing import List, Dict, Any, Union
from backend.core.db_manager import db_manager

class SessionManager:
    """Manages the creation and storage of study sessions from document content."""
    
    def __init__(self, document_data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        self.document_data = document_data
        
        if isinstance(document_data, dict):
            print(f"📄 SessionManager initialized with dict: {list(document_data.keys())}")
        elif isinstance(document_data, list):
            print(f"📄 SessionManager initialized with list of {len(document_data)} items")
        else:
            print(f"📄 SessionManager initialized with data: {type(document_data)}")

    def _flatten_all_segments(self) -> List[str]:
        """Extracts all segments/texts from the structured document."""
        all_segments = []
        
        if not self.document_data:
            print("⚠️  No document data available")
            return all_segments
        
        chapters = []
        
        if isinstance(self.document_data, list):
            chapters = self.document_data
            print(f"📖 Processing simplified format: {len(chapters)} chapters")
        elif isinstance(self.document_data, dict):
            chapters = self.document_data.get("chapters", [])
            print(f"📖 Processing Gemini format: {len(chapters)} chapters")
        
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                print(f"⚠️  Chapter {i} is not a dictionary: {type(chapter)}")
                continue
            
            # Find segments
            segments = chapter.get("segments", [])
            if segments:
                print(f"📝 Found {len(segments)} direct segments in chapter {i}")
                all_segments.extend(segments)
                continue
            
            # If not segments, process Gemini structure
            sections = chapter.get("sections", [])
            print(f"📝 Chapter {i} has {len(sections)} sections")
            
            for j, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                
                paragraphs = section.get("paragraphs", [])
                
                for paragraph in paragraphs:
                    if not isinstance(paragraph, dict):
                        continue
                    
                    lines = paragraph.get("lines", [])
                    all_segments.extend(lines)
        
        print(f"📊 Total segments extracted: {len(all_segments)}")
        
        filtered_segments = []
        for seg in all_segments:
            if seg and isinstance(seg, str):
                filtered_segments.append(seg.strip())
        
        print(f"📊 Segments after filtering: {len(filtered_segments)}")
        
        for i, seg in enumerate(filtered_segments[:3]):
            print(f"📄 Segment {i+1}: {seg[:50]}...")
        
        return filtered_segments

    def create_and_store_sessions_by_segments(self, user_id: int, document_id: int, segments_per_session: int) -> List[Dict[str, Any]]:
        """Creates study sessions by dividing content into chunks of n segments."""
        print(f"🎯 Starting session creation...")
        print(f"🎯 User ID: {user_id}, Document ID: {document_id}")
        print(f"🎯 Segments per session: {segments_per_session}")
        
        all_segments = self._flatten_all_segments()
        
        if not all_segments:
            print("❌ No segments found to create sessions")
            return []
        
        total_sessions = (len(all_segments) + segments_per_session - 1) // segments_per_session
        print(f"🎯 Creating {total_sessions} sessions from {len(all_segments)} total segments")
        
        sessions = []
        
        for i in range(total_sessions):
            start_idx = i * segments_per_session
            end_idx = start_idx + segments_per_session
            session_segments = all_segments[start_idx:end_idx]
            
            print(f"📦 Session {i+1}: segments {start_idx}-{end_idx} ({len(session_segments)} segments)")
            
            # Create session data
            session_data = {
                "title": f"Document {document_id} - Part {i+1}",
                "segments": session_segments
            }
            
            # Save session to JSON file
            session_filename = f"doc{document_id}_user{user_id}_session{i+1}.json"
            session_filepath = os.path.join(db_manager.DOC_STORAGE_PATH, session_filename)
            
            try:
                with open(session_filepath, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
                
                # Save to database
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    """INSERT INTO study_sessions 
                    (user_id, document_id, title, session_json_path, segment_count) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, document_id, session_data["title"], session_filepath, len(session_segments))
                )
                
                session_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                session_info = {
                    "session_id": session_id,
                    "title": session_data["title"],
                    "segment_count": len(session_segments)
                }
                
                sessions.append(session_info)
                print(f"✅ Session {i+1} saved (ID: {session_id})")
                
            except Exception as e:
                print(f"❌ Error saving session {i+1}: {e}")
                continue
        
        print(f"🎉 All sessions created: {len(sessions)} sessions")
        return sessions

    def create_sessions_by_chapters(self, user_id: int, document_id: int) -> List[Dict[str, Any]]:
        """Creates one session per document chapter."""
        print("⚠️  create_sessions_by_chapters not fully implemented")
        return []