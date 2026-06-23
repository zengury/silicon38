import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRobotContext } from '@/contexts/RobotContext';
import Button from '@/components/atoms/Button';
import CommentBubble from '@/components/molecules/CommentBubble';
import type { Comment } from '@/types';

export default function CollaborationPanel() {
  const { t } = useTranslation();
  const { comments, selectedRobotId, dispatch } = useRobotContext();
  const [input, setInput] = useState('');
  const [showMention, setShowMention] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const robotComments = selectedRobotId ? (comments[selectedRobotId] || []) : [];

  // Auto-scroll to bottom
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [robotComments.length]);

  // Detect @mention trigger
  function handleInputChange(value: string) {
    setInput(value);
    setShowMention(value.endsWith('@'));
  }

  function handleSend() {
    if (!input.trim() || !selectedRobotId) return;

    const newComment: Comment = {
      commentId: `comment-${Date.now()}`,
      robotId: selectedRobotId,
      authorId: 'current-user',
      authorName: '当前用户',
      content: input.trim(),
      mentions: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    dispatch({ type: 'ADD_COMMENT', robotId: selectedRobotId, comment: newComment });
    setInput('');
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleMarkHandling() {
    if (!selectedRobotId) return;
    dispatch({ type: 'MARK_HANDLING', robotId: selectedRobotId, userId: 'current-user', isHandling: true });
  }

  function handleMarkResolved() {
    if (!selectedRobotId) return;
    dispatch({ type: 'MARK_HANDLING', robotId: selectedRobotId, userId: 'current-user', isHandling: false });
  }

  if (!selectedRobotId) {
    return (
      <div className="card flex items-center justify-center h-full">
        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
          选择机器人后开始协作
        </p>
      </div>
    );
  }

  return (
    <div className="card flex flex-col h-full" role="region" aria-label={t('collaboration.title')}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
          {t('collaboration.title')} — <span className="font-mono">{selectedRobotId}</span>
        </h3>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleMarkHandling} style={{ fontSize: 11, padding: '3px 10px', height: 28 }}>
            {t('collaboration.imHandling')}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleMarkResolved} style={{ fontSize: 11, padding: '3px 10px', height: 28 }}>
            {t('collaboration.resolved')}
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto p-3">
        {robotComments.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-sm" style={{ color: 'var(--text-tertiary)' }}>
            {t('collaboration.noComments')}
          </div>
        ) : (
          robotComments.map((c) => (
            <CommentBubble key={c.commentId} comment={c} isCurrentUser={c.authorId === 'current-user'} />
          ))
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t" style={{ borderColor: 'var(--border-light)' }}>
        {showMention && (
          <div className="mb-2 p-2 rounded text-xs" style={{ backgroundColor: 'var(--bg-hover)' }}>
            <span className="font-medium">@王工</span>
            <span className="mx-2">·</span>
            <span className="font-medium">@李工</span>
            <span className="ml-2" style={{ color: 'var(--text-tertiary)' }}>{t('collaboration.atMention')}</span>
          </div>
        )}
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('collaboration.commentPlaceholder')}
            rows={2}
            className="flex-1 resize-none rounded-lg border px-3 py-2 text-sm outline-none transition-colors
              bg-[var(--bg-input)] border-[var(--border-default)] text-[var(--text-primary)]
              placeholder:text-[var(--text-tertiary)]
              focus:border-[var(--border-focus)] focus:ring-1 focus:ring-[var(--border-focus)]"
          />
          <Button onClick={handleSend} disabled={!input.trim()} className="self-end">
            {t('collaboration.send')}
          </Button>
        </div>
      </div>
    </div>
  );
}
