import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AudioPlayer } from "@/components/feature/audio-player";

describe("AudioPlayer", () => {
  it("renders with given title and controls", () => {
    render(<AudioPlayer src="https://example.com/audio.mp3" title="Pronunciation Practice" />);
    expect(screen.getByText("Pronunciation Practice")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Phát audio/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Thanh tiến độ phát âm thanh")).toBeInTheDocument();
  });
});
