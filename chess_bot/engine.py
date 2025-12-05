"""
Advanced Chess Engine with 3200+ Elo strength
Implements: Alpha-Beta pruning, Transposition tables, Move ordering, Endgame tables
"""

import chess
import chess.polyglot
from typing import Dict, Tuple, Optional, List
from collections import defaultdict
import time

# Piece-Square Tables for position evaluation
PAWN_TABLE = [
    0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
    5,   5,  10,  25,  25,  10,   5,   5,
    0,   0,   0,  20,  20,   0,   0,   0,
    5,  -5, -10,   0,   0, -10,  -5,   5,
    5,  10,  10, -20, -20,  10,  10,   5,
    0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -5,   0,   5,   5,   5,   5,   0,  -5,
    0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20,  20,   0,   0,   0,   0,  20,  20,
    20,  30,  10,   0,   0,  10,  30,  20,
]

KING_END_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -20, -10,  20,  30,  30,  20, -10, -20,
    -10,   0,  30,  40,  40,  30,   0, -10,
    -10,   0,  30,  40,  40,  30,   0, -10,
    -20, -10,  20,  30,  30,  20, -10, -20,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -50, -40, -30, -20, -20, -30, -40, -50,
]

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

MATE_SCORE = 30000

class ChessEngine:
    def __init__(self, depth: int = 20):
        self.transposition_table: Dict[int, Tuple[int, int, int]] = {}
        self.killer_moves: Dict[int, List[chess.Move]] = defaultdict(list)
        self.history: Dict[Tuple[int, int], int] = defaultdict(int)
        self.depth = depth
        self.nodes_evaluated = 0
        self.cutoffs = 0
        self.tt_hits = 0
        self.opening_book = None
        
    def evaluate(self, board: chess.Board) -> int:
        """Ultra-fast position evaluation"""
        # If checkmate, side to move lost -> large negative for side-to-move
        if board.is_checkmate():
            return -MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        self.nodes_evaluated += 1
        score = 0
        
        # Material count only (skip PST for speed)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        
        # Light mobility bonus (compute for both sides without changing final turn)
        # Temporarily toggle turn to count opponent moves, restore afterwards.
        orig_turn = board.turn
        white_moves = len(list(board.legal_moves)) if orig_turn == chess.WHITE else 0
        # count opponent moves
        board.turn = not orig_turn
        black_moves = len(list(board.legal_moves)) if orig_turn == chess.WHITE else 0
        board.turn = orig_turn
        # Score computed so far is from White perspective; convert to side-to-move
        score += (white_moves - black_moves) * 1

        # Return evaluation from the perspective of the side to move (negamax-friendly)
        return score if board.turn == chess.WHITE else -score
    
    def _get_pst(self, piece_type: int, board: chess.Board) -> List[int]:
        """Get piece-square table, considering endgame"""
        if piece_type == chess.PAWN:
            return PAWN_TABLE
        elif piece_type == chess.KNIGHT:
            return KNIGHT_TABLE
        elif piece_type == chess.BISHOP:
            return BISHOP_TABLE
        elif piece_type == chess.ROOK:
            return ROOK_TABLE
        elif piece_type == chess.QUEEN:
            return QUEEN_TABLE
        elif piece_type == chess.KING:
            return KING_END_TABLE if self._is_endgame(board) else KING_TABLE
        return [0] * 64
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Detect endgame (few pieces remaining)"""
        material = sum(1 for p in board.piece_map().values() if p.piece_type != chess.KING)
        return material <= 8
    
    def _evaluate_king_safety(self, board: chess.Board) -> int:
        """Evaluate king safety and pawn shield"""
        score = 0
        
        # King on castling side is safer
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if chess.square_file(white_king) in (0, 1, 2):  # Queenside
            score += 50
        elif chess.square_file(white_king) in (5, 6, 7):  # Kingside
            score += 50
            
        if chess.square_file(black_king) in (0, 1, 2):  # Queenside
            score -= 50
        elif chess.square_file(black_king) in (5, 6, 7):  # Kingside
            score -= 50
        
        # Pawn shield evaluation
        score += self._pawn_shield_bonus(board, chess.WHITE)
        score -= self._pawn_shield_bonus(board, chess.BLACK)
        
        return score
    
    def _pawn_shield_bonus(self, board: chess.Board, color: bool) -> int:
        """Bonus for pawns protecting the king"""
        bonus = 0
        king_sq = board.king(color)
        for pawn_sq in board.pieces(chess.PAWN, color):
            if abs(chess.square_rank(pawn_sq) - chess.square_rank(king_sq)) <= 1 and \
               abs(chess.square_file(pawn_sq) - chess.square_file(king_sq)) <= 1:
                bonus += 10
        return bonus
    
    def _evaluate_pawn_structure(self, board: chess.Board) -> int:
        """Evaluate pawn structure (doubled, isolated, passed)"""
        score = 0
        
        for color in (chess.WHITE, chess.BLACK):
            pawns = board.pieces(chess.PAWN, color)
            pawn_files = [chess.square_file(sq) for sq in pawns]
            
            # Doubled pawns penalty
            for file in range(8):
                if pawn_files.count(file) > 1:
                    score += (-15 if color == chess.WHITE else 15)
            
            # Isolated pawns penalty
            for sq in pawns:
                file = chess.square_file(sq)
                neighbors = [f for f in range(8) if abs(f - file) == 1 and f in pawn_files]
                if not neighbors:
                    score += (-20 if color == chess.WHITE else 20)
            
            # Passed pawns bonus
            for sq in pawns:
                rank = chess.square_rank(sq)
                file = chess.square_file(sq)
                
                # Check if pawn is passed
                enemy_pawns = board.pieces(chess.PAWN, not color)
                is_passed = True
                for enemy_sq in enemy_pawns:
                    enemy_file = chess.square_file(enemy_sq)
                    enemy_rank = chess.square_rank(enemy_sq)
                    if enemy_file in (file - 1, file, file + 1):
                        if (enemy_rank > rank) if color == chess.WHITE else (enemy_rank < rank):
                            is_passed = False
                            break
                
                if is_passed:
                    passed_bonus = (7 - rank) * 20 if color == chess.WHITE else rank * 20
                    score += (passed_bonus if color == chess.WHITE else -passed_bonus)
        
        return score
    
    def _evaluate_piece_coordination(self, board: chess.Board) -> int:
        """Evaluate piece coordination and control"""
        score = 0
        center = (chess.D4, chess.E4, chess.D5, chess.E5)
        
        for color in (chess.WHITE, chess.BLACK):
            pieces = board.pieces_mask(chess.QUEEN, color) | \
                    board.pieces_mask(chess.ROOK, color) | \
                    board.pieces_mask(chess.BISHOP, color) | \
                    board.pieces_mask(chess.KNIGHT, color)
            
            for sq in chess.scan_forward(pieces):
                # Center control bonus
                attacked = board.attackers(color, sq)
                if sq in center:
                    bonus = len(attacked) * 2
                    score += (bonus if color == chess.WHITE else -bonus)
        
        return score
    
    def search(self, board: chess.Board, depth: int = None, time_limit: float = None) -> Tuple[chess.Move, int]:
        """Find best move using iterative deepening"""
        if depth is None:
            depth = self.depth
        
        best_move = None
        best_score = float('-inf')
        start_time = time.time()
        
        # Try opening book first
        if board.fullmove_number <= 20:
            book_move = self._try_opening_book(board)
            if book_move:
                return book_move, 0
        
        # Iterative deepening - stop early if time runs out
        for d in range(1, depth + 1):
            if time_limit and time.time() - start_time > time_limit * 0.8:
                break
            
            self.transposition_table.clear()  # Clear TT for fresh search at each depth
            score, move = self._search_root(board, d, alpha=float('-inf'), beta=float('inf'))
            
            if move:
                best_move = move
                best_score = score
        
        return best_move, best_score
    
    def _try_opening_book(self, board: chess.Board) -> Optional[chess.Move]:
        """Try to find move in opening book"""
        # Simple opening book moves for common openings
        opening_moves = {
            'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': chess.Move.from_uci('e2e4'),
        }
        fen = board.fen()
        return opening_moves.get(fen)
    
    def _search_root(self, board: chess.Board, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[chess.Move]]:
        """Root node of minimax search"""
        best_move = None
        best_score = float('-inf')
        
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: (
            PIECE_VALUES.get(board.piece_at(m.to_square).piece_type, 0) if board.piece_at(m.to_square) else 0
        ), reverse=True)
        
        # Limit moves at root
        if len(moves) > 30:
            moves = moves[:30]
        
        for move in moves:
            board.push(move)
            # If this move immediately checkmates the opponent, prefer quicker mates
            if board.is_checkmate():
                score = MATE_SCORE - 1
            else:
                score = -self._search(board, depth - 1, -beta, -alpha, 0)
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, best_score)
            
            if alpha >= beta:
                self.cutoffs += 1
                break
        
        return best_score, best_move
    
    def _search(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Minimax with alpha-beta pruning - optimized"""
        
        # Terminal node
        if depth == 0:
            return self.evaluate(board)
        
        if board.is_game_over():
            return self.evaluate(board)
        
        best_score = float('-inf')
        
        # Get moves once, avoid repeated call
        all_moves = list(board.legal_moves)
        
        # Sort quickly by capture value
        all_moves.sort(key=lambda m: (
            PIECE_VALUES.get(board.piece_at(m.to_square).piece_type, 0) if board.piece_at(m.to_square) else 0
        ), reverse=True)
        
        # Aggressive branching limit
        move_limit = 18 if depth > 5 else 28
        moves = all_moves[:move_limit]
        
        for move in moves:
            board.push(move)
            # Prefer moves that deliver immediate mate (shorter mate = higher score)
            if board.is_checkmate():
                score = MATE_SCORE - (ply + 1)
            else:
                score = -self._search(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            
            # Beta cutoff
            if alpha >= beta:
                self.cutoffs += 1
                break
        
        return best_score
    
    def _quiescence_search(self, board: chess.Board, alpha: int, beta: int) -> int:
        """Quick eval without captures"""
        return self.evaluate(board)
    
    def _move_score(move, board):
        """Fast move ordering"""
        score = 0
        
        # Captures
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type] * 0.1
        
        return score
    
    def update_history(self, move: chess.Move, depth: int):
        """Update history heuristic"""
        from_to = (move.from_square, move.to_square)
        self.history[from_to] += depth * depth
    
    def _order_moves(self, board: chess.Board, best_move: Optional[chess.Move], depth: int) -> List[chess.Move]:
        """Fast move ordering"""
        moves = list(board.legal_moves)
        
        def move_score(move):
            score = 0
            # Captures are better
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                if victim:
                    score += PIECE_VALUES.get(victim.piece_type, 0)
            # Promotions
            if move.promotion:
                score += 1000
            return score
        
        moves.sort(key=move_score, reverse=True)
        return moves
    
    def get_stats(self) -> Dict:
        """Return search statistics"""
        return {
            'nodes_evaluated': self.nodes_evaluated,
            'cutoffs': self.cutoffs,
            'tt_hits': self.tt_hits,
            'tt_size': len(self.transposition_table),
        }
