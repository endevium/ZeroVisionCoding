import {
  MediaControlBar,
  MediaController,
  MediaMuteButton,
  MediaPlayButton,
  MediaSeekBackwardButton,
  MediaSeekForwardButton,
  MediaTimeDisplay,
  MediaTimeRange,
  MediaVolumeRange,
} from "media-chrome/react"
import type { ComponentProps, CSSProperties } from "react"
import { cn } from "@/lib/utils"

export type VideoPlayerProps = ComponentProps<typeof MediaController>

const variables = {
  "--media-primary-color": "var(--primary)",
  "--media-secondary-color": "var(--background)",
  "--media-text-color": "var(--foreground)",
  "--media-background-color": "var(--background)",
  "--media-control-hover-background": "var(--accent)",
  "--media-font-family": "var(--font-sans)",
  "--media-live-button-icon-color": "var(--muted-foreground)",
  "--media-live-button-indicator-color": "var(--destructive)",
  "--media-range-track-background": "var(--border)",
} as CSSProperties

export const VideoPlayer = ({ style, ...props }: VideoPlayerProps) => (
  <MediaController
    style={{
      ...variables,
      ...style,
    }}
    {...(props as any)}
  />
)

export type VideoPlayerControlBarProps = ComponentProps<typeof MediaControlBar>

export const VideoPlayerControlBar = (props: VideoPlayerControlBarProps) => (
  <MediaControlBar {...(props as any)} />
)

export type VideoPlayerTimeRangeProps = ComponentProps<typeof MediaTimeRange>

export const VideoPlayerTimeRange = ({ className, ...props }: VideoPlayerTimeRangeProps) => (
  <MediaTimeRange className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerTimeDisplayProps = ComponentProps<typeof MediaTimeDisplay>

export const VideoPlayerTimeDisplay = ({ className, ...props }: VideoPlayerTimeDisplayProps) => (
  <MediaTimeDisplay className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerVolumeRangeProps = ComponentProps<typeof MediaVolumeRange>

export const VideoPlayerVolumeRange = ({ className, ...props }: VideoPlayerVolumeRangeProps) => (
  <MediaVolumeRange className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerPlayButtonProps = ComponentProps<typeof MediaPlayButton>

export const VideoPlayerPlayButton = ({ className, ...props }: VideoPlayerPlayButtonProps) => (
  <MediaPlayButton className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerSeekBackwardButtonProps = ComponentProps<typeof MediaSeekBackwardButton>

export const VideoPlayerSeekBackwardButton = ({
  className,
  ...props
}: VideoPlayerSeekBackwardButtonProps) => (
  <MediaSeekBackwardButton className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerSeekForwardButtonProps = ComponentProps<typeof MediaSeekForwardButton>

export const VideoPlayerSeekForwardButton = ({
  className,
  ...props
}: VideoPlayerSeekForwardButtonProps) => (
  <MediaSeekForwardButton className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerMuteButtonProps = ComponentProps<typeof MediaMuteButton>

export const VideoPlayerMuteButton = ({ className, ...props }: VideoPlayerMuteButtonProps) => (
  <MediaMuteButton className={cn("p-2.5", className)} {...(props as any)} />
)

export type VideoPlayerContentProps = ComponentProps<"video">

export const VideoPlayerContent = ({ className, ...props }: VideoPlayerContentProps) => (
  <video className={cn("mt-0 mb-0", className)} {...(props as any)} />
)

// Demo
export function Demo() {
  return (
    <div className="flex w-full h-[68vh] aspect-video items-center justify-center">
      <div className="w-full h-full max-w-6xl">
          <VideoPlayer className="w-full h-full rounded-lg border overflow-hidden">
          <video
            slot="media"
            src="https://stream.mux.com/VZtzUzGRv02OhRnZCxcNg49OilvolTqdnFLEqBsTwaxU/high.mp4"
            poster="https://image.mux.com/VZtzUzGRv02OhRnZCxcNg49OilvolTqdnFLEqBsTwaxU/thumbnail.webp?time=0"
            suppressHydrationWarning
          />
          <VideoPlayerControlBar>
            <VideoPlayerPlayButton />
            <VideoPlayerTimeRange />
            <VideoPlayerTimeDisplay />
            <VideoPlayerMuteButton />
            <VideoPlayerVolumeRange />
          </VideoPlayerControlBar>
        </VideoPlayer>
      </div>
    </div>
  )
}

export function FirstFeature() {
  return (
    <div className="flex w-full h-full items-center justify-center">
      <div className="w-full h-full max-w-5xl">
          <VideoPlayer className="w-full h-full rounded-lg overflow-hidden">
          <video
            slot="media"
            src="https://stream.mux.com/VZtzUzGRv02OhRnZCxcNg49OilvolTqdnFLEqBsTwaxU/high.mp4"
            poster="https://image.mux.com/VZtzUzGRv02OhRnZCxcNg49OilvolTqdnFLEqBsTwaxU/thumbnail.webp?time=0"
            suppressHydrationWarning
          />
          <VideoPlayerControlBar>
            <VideoPlayerPlayButton />
            <VideoPlayerTimeRange />
            <VideoPlayerTimeDisplay />
            <VideoPlayerMuteButton />
            <VideoPlayerVolumeRange />
          </VideoPlayerControlBar>
        </VideoPlayer>
      </div>
    </div>
  )
}