"use client";

import * as React from "react";
import { Volume2, Play, Pause } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface AudioPlayerProps {
  src: string;
  title?: string;
  className?: string;
}

export function AudioPlayer({ src, title = "Luyện nghe bài học", className }: AudioPlayerProps) {
  const audioRef = React.useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);

  function togglePlay() {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }

  function handleTimeUpdate() {
    if (!audioRef.current) return;
    setCurrentTime(audioRef.current.currentTime);
  }

  function handleLoadedMetadata() {
    if (!audioRef.current) return;
    setDuration(audioRef.current.duration);
  }

  function handleSeek(e: React.ChangeEvent<HTMLInputElement>) {
    const time = Number(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  }

  function handleEnded() {
    setIsPlaying(false);
    setCurrentTime(0);
  }

  function formatTime(seconds: number): string {
    if (isNaN(seconds) || seconds === 0) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border bg-surface-2/60 p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between sm:gap-6",
        className,
      )}
    >
      <audio
        ref={audioRef}
        src={src}
        preload="none"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
      />

      <div className="flex items-center gap-3">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={togglePlay}
          aria-label={isPlaying ? "Tạm dừng audio" : "Phát audio"}
          className="size-10 rounded-full p-0 shrink-0"
        >
          {isPlaying ? (
            <Pause className="size-4 text-primary" aria-hidden />
          ) : (
            <Play className="size-4 ml-0.5 text-primary" aria-hidden />
          )}
        </Button>

        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-body-sm font-semibold text-text truncate">
            <Volume2 className="size-4 text-primary shrink-0" aria-hidden />
            <span className="truncate">{title}</span>
          </div>
          <div className="text-xs text-text-muted">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>
      </div>

      <div className="flex flex-1 items-center gap-2">
        <input
          type="range"
          min={0}
          max={duration || 100}
          value={currentTime}
          onChange={handleSeek}
          className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-border accent-primary"
          aria-label="Thanh tiến độ phát âm thanh"
        />
      </div>
    </div>
  );
}
