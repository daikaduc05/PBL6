import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "./button";

describe("Button", () => {
  it("renders its label", () => {
    render(<Button>Lưu thay đổi</Button>);
    expect(screen.getByRole("button", { name: "Lưu thay đổi" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled and non-clickable while loading", () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Đăng nhập
      </Button>,
    );
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("asChild renders the child element instead of a <button>", () => {
    render(
      <Button asChild>
        <a href="/checkout">Nâng cấp VIP</a>
      </Button>,
    );
    const link = screen.getByRole("link", { name: "Nâng cấp VIP" });
    expect(link).toBeInTheDocument();
    expect(link.tagName).toBe("A");
  });
});
