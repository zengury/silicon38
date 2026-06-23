import { formatDate } from '@/lib/mockData';
import type { Comment as CommentType } from '@/types';

interface CommentBubbleProps {
  comment: CommentType;
  isCurrentUser?: boolean;
}

export default function CommentBubble({ comment, isCurrentUser }: CommentBubbleProps) {
  return (
    <div className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isCurrentUser
            ? 'rounded-br-sm'
            : 'rounded-bl-sm'
        }`}
        style={{
          backgroundColor: isCurrentUser ? '#2563EB' : 'var(--bg-hover)',
          color: isCurrentUser ? '#FFFFFF' : 'var(--text-primary)',
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium opacity-80">{comment.authorName}</span>
          <span className="text-[10px] opacity-60" style={{ color: isCurrentUser ? 'rgba(255,255,255,0.7)' : undefined }}>
            {formatDate(comment.createdAt)}
          </span>
        </div>
        <p className="whitespace-pre-wrap break-words">{comment.content}</p>
        {comment.mentions.length > 0 && (
          <div className="flex gap-1 mt-1">
            {comment.mentions.map((m) => (
              <span key={m} className="text-[10px] px-1.5 py-0.5 rounded-full bg-black/10">
                @{m}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
