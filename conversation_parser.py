"""
Conversation Parser for Mud Room Protocol v2.0
Intelligently chunks conversations into meaningful blocks for classification
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from semantic_scorer import SemanticScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationBlock:
    """A chunk of conversation to be classified"""
    text: str
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    line_numbers: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    block_type: str = "general"  # general, question, answer, decision, etc.


class ConversationParser:
    """
    Intelligently parses conversations into meaningful blocks for classification
    """
    
    def __init__(self, min_block_size: int = 50, max_block_size: int = 2000):
        """
        Initialize the conversation parser
        
        Args:
            min_block_size: Minimum characters for a block
            max_block_size: Maximum characters for a block
        """
        self.min_block_size = min_block_size
        self.max_block_size = max_block_size
        self.semantic_scorer = SemanticScorer()
        
        # Pre-compile regex patterns for performance
        self.speaker_patterns = [
            re.compile(r'^(You said:|ChatGPT said:|User:|Assistant:|AI:)', re.IGNORECASE),
            re.compile(r'^([A-Z][a-z]+ said:)', re.IGNORECASE),
            re.compile(r'^(Human:|Bot:)', re.IGNORECASE)
        ]
        
        self.timestamp_patterns = [
            re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'),
            re.compile(r'(\d{2}:\d{2}:\d{2})'),
            re.compile(r'(\d{4}-\d{2}-\d{2})')
        ]
        
        self.context_shift_patterns = [
            re.compile(r'(by the way|so anyway|moving on|next topic|speaking of)', re.IGNORECASE),
            re.compile(r'(I\'m back|let\'s continue|resuming|back to)', re.IGNORECASE),
            re.compile(r'(new goal:|next task:|new objective:)', re.IGNORECASE),
            re.compile(r'(sleep well|signing off|goodbye|end session)', re.IGNORECASE)
        ]
        
        self.decision_patterns = [
            re.compile(r'(we will|we\'ve decided|going forward|committed to)', re.IGNORECASE),
            re.compile(r'(final choice|decision made|settled on)', re.IGNORECASE),
            re.compile(r'(strategy:|vision:|direction:)', re.IGNORECASE)
        ]
        
        self.question_patterns = [
            re.compile(r'\?$'),  # Ends with question mark
            re.compile(r'(can you|could you|would you|how do|what is|why does)', re.IGNORECASE),
            re.compile(r'(I wonder|I\'m curious|let me ask)', re.IGNORECASE)
        ]
    
    def parse_conversation(self, file_path: str) -> List[ConversationBlock]:
        """
        Parse a conversation file into meaningful blocks
        
        Args:
            file_path: Path to the conversation file
            
        Returns:
            List of conversation blocks
        """
        logger.info(f"Starting to parse conversation file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logger.info(f"Loaded {len(lines)} lines from file")
        
        # For very large files, use optimized parsing
        if len(lines) > 10000:
            logger.info("Large file detected, using optimized parsing strategy")
            return self._parse_large_file(lines)
        else:
            # Use standard parsing for smaller files
            return self._parse_standard(lines)
    
    def _parse_large_file(self, lines: List[str]) -> List[ConversationBlock]:
        """
        Optimized parsing for large files (>10,000 lines)
        """
        logger.info("Using optimized parsing for large file")
        
        blocks = []
        current_block_lines = []
        current_speaker = None
        current_timestamp = None
        line_count = 0
        skipped_lines = 0
        
        # Pre-filter: remove empty lines and count them
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                filtered_lines.append(stripped)
            else:
                skipped_lines += 1
        
        logger.info(f"Pre-filtered: {len(lines)} → {len(filtered_lines)} lines (skipped {skipped_lines} empty lines)")
        
        # Process lines in batches for better performance
        batch_size = 1000
        total_batches = (len(filtered_lines) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(filtered_lines))
            batch_lines = filtered_lines[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} (lines {start_idx + 1}-{end_idx})")
            
            for i, line in enumerate(batch_lines):
                line_num = start_idx + i + 1
                
                # Ultra-fast speaker detection using string operations first
                speaker = self._ultra_fast_speaker_detect(line)
                timestamp = self._ultra_fast_timestamp_detect(line)
                
                # Check if we should start a new block
                should_start_new = (
                    speaker and speaker != current_speaker or
                    timestamp or
                    len(' '.join(current_block_lines)) > self.max_block_size or
                    self._ultra_fast_context_shift_detect(line)
                )
                
                if should_start_new and current_block_lines:
                    # Create block from accumulated lines
                    block_text = ' '.join(current_block_lines)
                    if len(block_text.strip()) >= self.min_block_size:
                        block = ConversationBlock(
                            text=block_text,
                            speaker=current_speaker,
                            timestamp=current_timestamp,
                            line_numbers=list(range(line_count - len(current_block_lines) + 1, line_count + 1))
                        )
                        blocks.append(block)
                    
                    # Start new block
                    current_block_lines = []
                    current_speaker = speaker
                    current_timestamp = timestamp
                
                # Add line to current block
                if speaker:
                    # Remove speaker prefix from content using string operations
                    content = self._remove_speaker_prefix(line, speaker)
                    current_block_lines.append(content)
                else:
                    current_block_lines.append(line)
                
                line_count += 1
                
                # Progress logging for very large files
                if line_count % 5000 == 0:
                    logger.info(f"Processed {line_count}/{len(filtered_lines)} lines, created {len(blocks)} blocks")
        
        # Create final block
        if current_block_lines:
            block_text = ' '.join(current_block_lines)
            if len(block_text.strip()) >= self.min_block_size:
                block = ConversationBlock(
                    text=block_text,
                    speaker=current_speaker,
                    timestamp=current_timestamp,
                    line_numbers=list(range(line_count - len(current_block_lines) + 1, line_count + 1))
                )
                blocks.append(block)
        
        logger.info(f"Optimized parsing complete: {len(lines)} lines → {len(blocks)} blocks (skipped {skipped_lines} empty lines)")
        return blocks
    
    def _parse_standard(self, lines: List[str]) -> List[ConversationBlock]:
        """
        Standard parsing for smaller files
        """
        # First pass: identify speakers and timestamps
        parsed_lines = self._parse_lines(lines)
        
        # Second pass: group into blocks
        blocks = self._create_blocks(parsed_lines)
        
        # Third pass: merge similar blocks and split large ones
        blocks = self._optimize_blocks(blocks)
        
        logger.info(f"Standard parsing complete: {len(lines)} lines → {len(blocks)} blocks")
        return blocks
    
    def _parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse individual lines to extract speaker, timestamp, and content
        
        Args:
            lines: Raw lines from the conversation file
            
        Returns:
            List of parsed line dictionaries
        """
        parsed_lines = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            parsed_line = {
                'line_number': i,
                'raw_text': line,
                'speaker': None,
                'timestamp': None,
                'content': line,
                'block_type': 'general'
            }
            
            # Extract speaker
            for pattern in self.speaker_patterns:
                match = pattern.match(line)
                if match:
                    parsed_line['speaker'] = match.group(1).rstrip(':').strip()
                    parsed_line['content'] = line[match.end():].strip()
                    break
            
            # Extract timestamp
            for pattern in self.timestamp_patterns:
                match = pattern.search(line)
                if match:
                    parsed_line['timestamp'] = match.group(1)
                    break
            
            # Detect block type
            parsed_line['block_type'] = self._detect_block_type(parsed_line['content'])
            
            parsed_lines.append(parsed_line)
        
        return parsed_lines
    
    def _detect_block_type(self, content: str) -> str:
        """
        Detect the type of conversation block
        
        Args:
            content: The content of the block
            
        Returns:
            Block type (general, question, answer, decision, etc.)
        """
        content_lower = content.lower()
        
        # Check for decisions
        for pattern in self.decision_patterns:
            if pattern.search(content_lower):
                return "decision"
        
        # Check for questions
        for pattern in self.question_patterns:
            if pattern.search(content_lower):
                return "question"
        
        # Check for context shifts
        for pattern in self.context_shift_patterns:
            if pattern.search(content_lower):
                return "context_shift"
        
        return "general"
    
    def _create_blocks(self, parsed_lines: List[Dict[str, Any]]) -> List[ConversationBlock]:
        """
        Group parsed lines into conversation blocks
        
        Args:
            parsed_lines: List of parsed line dictionaries
            
        Returns:
            List of conversation blocks
        """
        blocks = []
        current_block = None
        
        for line_data in parsed_lines:
            # Check if we should start a new block
            should_start_new = self._should_start_new_block(current_block, line_data)
            
            if should_start_new:
                # Save current block if it exists
                if current_block and len(current_block.text.strip()) >= self.min_block_size:
                    blocks.append(current_block)
                
                # Start new block
                current_block = ConversationBlock(
                    text=line_data['content'],
                    speaker=line_data['speaker'],
                    timestamp=line_data['timestamp'],
                    line_numbers=[line_data['line_number']],
                    block_type=line_data['block_type'],
                    metadata={'block_type': line_data['block_type']}
                )
            else:
                # Add to current block
                if current_block:
                    current_block.text += "\n" + line_data['content']
                    current_block.line_numbers.append(line_data['line_number'])
                    
                    # Update speaker if not set
                    if not current_block.speaker and line_data['speaker']:
                        current_block.speaker = line_data['speaker']
                    
                    # Update timestamp if not set
                    if not current_block.timestamp and line_data['timestamp']:
                        current_block.timestamp = line_data['timestamp']
        
        # Add final block
        if current_block and len(current_block.text.strip()) >= self.min_block_size:
            blocks.append(current_block)
        
        return blocks
    
    def _should_start_new_block(self, current_block: Optional[ConversationBlock], 
                               line_data: Dict[str, Any]) -> bool:
        """
        Determine if a new block should be started
        
        Args:
            current_block: Current conversation block
            line_data: Data for the current line
            
        Returns:
            True if a new block should be started
        """
        # Always start new block if none exists
        if not current_block:
            return True
        
        # Start new block for context shifts
        if line_data['block_type'] == 'context_shift':
            return True
        
        # Start new block for decisions
        if line_data['block_type'] == 'decision':
            return True
        
        # Start new block if speaker changes
        if (current_block.speaker and line_data['speaker'] and 
            current_block.speaker != line_data['speaker']):
            return True
        
        # Start new block if current block is getting too large
        if len(current_block.text) > self.max_block_size:
            return True
        
        # Start new block if there's a significant time gap
        if (current_block.timestamp and line_data['timestamp'] and
            self._time_gap_significant(current_block.timestamp, line_data['timestamp'])):
            return True
        
        return False
    
    def _time_gap_significant(self, timestamp1: str, timestamp2: str) -> bool:
        """
        Check if there's a significant time gap between timestamps
        
        Args:
            timestamp1: First timestamp
            timestamp2: Second timestamp
            
        Returns:
            True if the gap is significant
        """
        try:
            # Try to parse timestamps
            if len(timestamp1) == 19:  # Full datetime
                dt1 = datetime.strptime(timestamp1, "%Y-%m-%d %H:%M:%S")
            elif len(timestamp1) == 8:  # Time only
                dt1 = datetime.strptime(timestamp1, "%H:%M:%S")
            else:
                return False
            
            if len(timestamp2) == 19:  # Full datetime
                dt2 = datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S")
            elif len(timestamp2) == 8:  # Time only
                dt2 = datetime.strptime(timestamp2, "%H:%M:%S")
            else:
                return False
            
            # Consider gap significant if more than 5 minutes
            time_diff = abs((dt2 - dt1).total_seconds())
            return time_diff > 300  # 5 minutes
            
        except ValueError:
            return False
    
    def _optimize_blocks(self, blocks: List[ConversationBlock]) -> List[ConversationBlock]:
        """
        Optimize blocks by merging similar ones and splitting large ones
        
        Args:
            blocks: List of conversation blocks
            
        Returns:
            Optimized list of conversation blocks
        """
        optimized_blocks = []
        
        for block in blocks:
            # Split large blocks
            if len(block.text) > self.max_block_size:
                sub_blocks = self._split_large_block(block)
                optimized_blocks.extend(sub_blocks)
            else:
                optimized_blocks.append(block)
        
        # Merge similar blocks
        optimized_blocks = self._merge_similar_blocks(optimized_blocks)
        
        return optimized_blocks
    
    def _split_large_block(self, block: ConversationBlock) -> List[ConversationBlock]:
        """
        Split a large block into smaller, meaningful chunks
        
        Args:
            block: The large block to split
            
        Returns:
            List of smaller blocks
        """
        # Split by sentences first
        sentences = re.split(r'[.!?]+', block.text)
        sub_blocks = []
        current_text = ""
        current_lines = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would make the block too large, start a new one
            if len(current_text) + len(sentence) > self.max_block_size and current_text:
                sub_block = ConversationBlock(
                    text=current_text.strip(),
                    speaker=block.speaker,
                    timestamp=block.timestamp,
                    line_numbers=current_lines.copy(),
                    block_type=block.block_type,
                    metadata=block.metadata
                )
                sub_blocks.append(sub_block)
                current_text = sentence
                current_lines = []
            else:
                current_text += " " + sentence if current_text else sentence
        
        # Add the last block
        if current_text.strip():
            sub_block = ConversationBlock(
                text=current_text.strip(),
                speaker=block.speaker,
                timestamp=block.timestamp,
                line_numbers=current_lines,
                block_type=block.block_type,
                metadata=block.metadata
            )
            sub_blocks.append(sub_block)
        
        return sub_blocks
    
    def _merge_similar_blocks(self, blocks: List[ConversationBlock]) -> List[ConversationBlock]:
        """
        Merge blocks that are semantically similar
        
        Args:
            blocks: List of conversation blocks
            
        Returns:
            List of merged blocks
        """
        if len(blocks) <= 1:
            return blocks
        
        merged_blocks = []
        i = 0
        
        while i < len(blocks):
            current_block = blocks[i]
            merged = False
            
            # Try to merge with next block if they're similar
            if i + 1 < len(blocks):
                next_block = blocks[i + 1]
                
                # Check if blocks should be merged
                if self._should_merge_blocks(current_block, next_block):
                    # Merge the blocks
                    merged_block = ConversationBlock(
                        text=current_block.text + "\n" + next_block.text,
                        speaker=current_block.speaker or next_block.speaker,
                        timestamp=current_block.timestamp or next_block.timestamp,
                        line_numbers=current_block.line_numbers + next_block.line_numbers,
                        block_type=current_block.block_type,
                        metadata=current_block.metadata
                    )
                    merged_blocks.append(merged_block)
                    i += 2  # Skip next block
                    merged = True
            
            if not merged:
                merged_blocks.append(current_block)
                i += 1
        
        return merged_blocks
    
    def _should_merge_blocks(self, block1: ConversationBlock, block2: ConversationBlock) -> bool:
        """
        Determine if two blocks should be merged
        
        Args:
            block1: First block
            block2: Second block
            
        Returns:
            True if blocks should be merged
        """
        # Don't merge if combined size would be too large
        if len(block1.text) + len(block2.text) > self.max_block_size:
            return False
        
        # Don't merge if speakers are different
        if (block1.speaker and block2.speaker and 
            block1.speaker != block2.speaker):
            return False
        
        # Don't merge if one is a context shift or decision
        if (block1.block_type in ['context_shift', 'decision'] or 
            block2.block_type in ['context_shift', 'decision']):
            return False
        
        # Merge if blocks are semantically similar
        similarity = self.semantic_scorer.calculate_context_similarity(
            block1.text, block2.text
        )
        
        return similarity > 0.7  # High similarity threshold for merging
    
    def _ultra_fast_speaker_detect(self, line: str) -> Optional[str]:
        """
        Ultra-fast speaker detection using string operations first
        """
        # Check most common patterns using string operations (faster than regex)
        if line.startswith('You said:'):
            return 'You'
        elif line.startswith('ChatGPT said:'):
            return 'ChatGPT'
        elif line.startswith('User:'):
            return 'User'
        elif line.startswith('Assistant:'):
            return 'Assistant'
        elif line.startswith('AI:'):
            return 'AI'
        elif line.startswith('Human:'):
            return 'Human'
        elif line.startswith('Bot:'):
            return 'Bot'
        
        # Fallback to regex for less common patterns
        for pattern in self.speaker_patterns:
            match = pattern.match(line)
            if match:
                return match.group(1).rstrip(':').strip()
        
        return None
    
    def _ultra_fast_timestamp_detect(self, line: str) -> Optional[str]:
        """
        Ultra-fast timestamp detection using string operations first
        """
        # Quick string checks for common timestamp patterns
        if '2025-' in line or '2024-' in line:
            # Look for full datetime pattern
            for pattern in self.timestamp_patterns:
                match = pattern.search(line)
                if match:
                    return match.group(1)
        elif ':' in line and len(line) >= 8:
            # Look for time-only pattern
            parts = line.split()
            for part in parts:
                if ':' in part and len(part) == 8 and part.count(':') == 2:
                    try:
                        # Validate it's actually a time
                        hour, minute, second = part.split(':')
                        if 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59 and 0 <= int(second) <= 59:
                            return part
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _ultra_fast_context_shift_detect(self, line: str) -> bool:
        """
        Ultra-fast context shift detection using string operations
        """
        line_lower = line.lower()
        
        # Most common context shift phrases
        if any(phrase in line_lower for phrase in [
            'by the way', 'so anyway', 'moving on', 'next topic',
            'I\'m back', 'let\'s continue', 'new goal:', 'next task:'
        ]):
            return True
        
        return False
    
    def _remove_speaker_prefix(self, line: str, speaker: str) -> str:
        """
        Remove speaker prefix from line using string operations
        """
        if not speaker:
            return line
        
        # Common speaker prefixes
        prefixes = [
            f"{speaker}:",
            f"{speaker} said:",
            f"{speaker} says:"
        ]
        
        for prefix in prefixes:
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        
        return line


if __name__ == "__main__":
    # Test the conversation parser
    parser = ConversationParser()
    
    # Test with a sample conversation
    test_conversation = """You said: Can you help me debug this error?
ChatGPT said: Sure! What error are you seeing?
You said: The server is returning a 500 error when I try to access the endpoint.
ChatGPT said: Let's check the server logs first. Can you show me the error message?
You said: Here's the error: "Internal server error - database connection failed"
ChatGPT said: That's a database connection issue. Let's verify the connection string and credentials.
You said: I think I found the issue - the database password was incorrect.
ChatGPT said: Great! That should fix it. Let's test the endpoint again.
You said: Perfect! It's working now. Thanks for the help.
ChatGPT said: You're welcome! Remember to always check credentials first when you see database connection errors."""
    
    # Write test conversation to file
    with open("test_conversation.txt", "w") as f:
        f.write(test_conversation)
    
    # Parse the conversation
    blocks = parser.parse_conversation("test_conversation.txt")
    
    print(f"Parsed {len(blocks)} conversation blocks:")
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}:")
        print(f"  Speaker: {block.speaker}")
        print(f"  Type: {block.block_type}")
        print(f"  Lines: {block.line_numbers}")
        print(f"  Text: {block.text[:100]}...")
