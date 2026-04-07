import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./accordion";
import { Card, CardAction, CardContent, CardFooter, CardHeader, CardTitle } from "./card";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "./command";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { Progress } from "./progress";
import { RadioGroup, RadioGroupItem } from "./radio-group";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "./select";
import { WizardContainer } from "./wizard-container";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(globalThis, "ResizeObserver", {
  configurable: true,
  writable: true,
  value: ResizeObserverMock,
});

Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
  configurable: true,
  writable: true,
  value: vi.fn(),
});

describe("ui primitives", () => {
  it("renders accordion content after expanding a trigger", () => {
    render(
      <Accordion collapsible type="single">
        <AccordionItem value="item-1">
          <AccordionTrigger>Section title</AccordionTrigger>
          <AccordionContent>Accordion body</AccordionContent>
        </AccordionItem>
      </Accordion>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Section title" }));

    expect(screen.getByText("Accordion body")).toBeInTheDocument();
  });

  it("renders command primitives inside an open command dialog", () => {
    render(
      <CommandDialog open onOpenChange={vi.fn()}>
        <CommandInput placeholder="Search commands" />
        <CommandList>
          <CommandEmpty>No results</CommandEmpty>
          <CommandGroup heading="General">
            <CommandItem>
              Open settings
              <CommandShortcut>Cmd+K</CommandShortcut>
            </CommandItem>
          </CommandGroup>
          <CommandSeparator />
        </CommandList>
      </CommandDialog>,
    );

    expect(screen.getByPlaceholderText("Search commands")).toBeInTheDocument();
    expect(screen.getByText("Open settings")).toBeInTheDocument();
    expect(screen.getByText("Cmd+K")).toBeInTheDocument();
  });

  it("renders a standalone command root", () => {
    render(
      <Command>
        <CommandList>
          <CommandItem>Standalone item</CommandItem>
        </CommandList>
      </Command>,
    );

    expect(screen.getByText("Standalone item")).toBeInTheDocument();
  });

  it("opens dropdown menu content and supports radio selection", () => {
    render(
      <DropdownMenu onOpenChange={vi.fn()} open>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuItem>Refresh</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuRadioGroup value="a">
            <DropdownMenuRadioItem value="a">Option A</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="b">Option B</DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
          <DropdownMenuItem>
            Archive
            <DropdownMenuShortcut>Shift+A</DropdownMenuShortcut>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(screen.getByText("Actions")).toBeInTheDocument();
    expect(screen.getByText("Refresh")).toBeInTheDocument();
    expect(screen.getByText("Option A")).toBeInTheDocument();
    expect(screen.getByText("Shift+A")).toBeInTheDocument();
  });

  it("renders advanced dropdown slots including group/checkbox/sub/portal", () => {
    render(
      <DropdownMenu open onOpenChange={vi.fn()}>
        <DropdownMenuTrigger>Open advanced menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuPortal>
            <span>portal-child</span>
          </DropdownMenuPortal>
          <DropdownMenuGroup>
            <DropdownMenuCheckboxItem checked>Remember choice</DropdownMenuCheckboxItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger inset>More actions</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuItem>Nested item</DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(screen.getByText("portal-child")).toBeInTheDocument();
    expect(screen.getByText("Remember choice")).toBeInTheDocument();
    expect(screen.getByText("More actions")).toBeInTheDocument();
    fireEvent.pointerMove(screen.getByText("More actions"));
    expect(screen.getByText("More actions")).toBeInTheDocument();
  });

  it("renders select group label and separator slots", () => {
    render(
      <Select defaultValue="alpha" open onOpenChange={vi.fn()}>
        <SelectTrigger>
          <SelectValue placeholder="Pick one" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Group label</SelectLabel>
            <SelectItem value="alpha">Alpha</SelectItem>
            <SelectSeparator />
            <SelectItem value="beta">Beta</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByText("Group label")).toBeInTheDocument();
    expect(screen.getAllByText("Alpha").length).toBeGreaterThan(0);
    expect(screen.getByText("Beta")).toBeInTheDocument();
  });

  it("applies destructive/inset dropdown attrs and compact select trigger size", () => {
    render(
      <>
        <DropdownMenu open onOpenChange={vi.fn()}>
          <DropdownMenuTrigger>Open custom menu</DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem inset variant="destructive">
              Delete item
            </DropdownMenuItem>
            <DropdownMenuLabel inset>Danger zone</DropdownMenuLabel>
          </DropdownMenuContent>
        </DropdownMenu>
        <Select defaultValue="beta" open onOpenChange={vi.fn()}>
          <SelectTrigger size="sm">
            <SelectValue placeholder="Pick one" />
          </SelectTrigger>
          <SelectContent position="item-aligned">
            <SelectItem value="beta">Beta</SelectItem>
          </SelectContent>
        </Select>
      </>,
    );

    const destructiveItem = screen
      .getByText("Delete item")
      .closest('[data-slot="dropdown-menu-item"]');
    expect(destructiveItem).not.toBeNull();
    expect(destructiveItem).toHaveAttribute("data-variant", "destructive");
    expect(destructiveItem).toHaveAttribute("data-inset", "true");
    expect(screen.getByText("Danger zone")).toHaveAttribute("data-inset", "true");
    expect(screen.getByRole("combobox", { hidden: true })).toHaveAttribute("data-size", "sm");
  });

  it("renders card action/footer slots", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card title</CardTitle>
          <CardAction>Action</CardAction>
        </CardHeader>
        <CardContent>Card body</CardContent>
        <CardFooter>Card footer</CardFooter>
      </Card>,
    );

    expect(screen.getByText("Card title")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Card body")).toBeInTheDocument();
    expect(screen.getByText("Card footer")).toBeInTheDocument();
  });

  it("opens popover content from trigger", () => {
    render(
      <Popover>
        <PopoverTrigger>Open popover</PopoverTrigger>
        <PopoverContent>Popover body</PopoverContent>
      </Popover>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open popover" }));

    expect(screen.getByText("Popover body")).toBeInTheDocument();
  });

  it("renders progress indicator transform from value", () => {
    const { container } = render(<Progress value={35} />);

    expect(container.querySelector('[data-slot="progress-indicator"]')).toHaveStyle({
      transform: "translateX(-65%)",
    });
  });

  it("renders wizard container and clicks completed step", () => {
    const onStepClick = vi.fn();

    render(
      <WizardContainer
        currentStep={2}
        onStepClick={onStepClick}
        steps={[
          { number: 1, title: "First", description: "Choose type" },
          { number: 2, title: "Second", description: "Review" },
        ]}
      >
        <div>Wizard body</div>
      </WizardContainer>,
    );

    fireEvent.click(screen.getByRole("button", { name: /First/ }));

    expect(onStepClick).toHaveBeenCalledWith(1);
    expect(screen.getByText("Wizard body")).toBeInTheDocument();
  });

  it("renders radio group items and toggles selection", () => {
    render(
      <RadioGroup defaultValue="one">
        <label>
          <RadioGroupItem value="one" />
          One
        </label>
        <label>
          <RadioGroupItem value="two" />
          Two
        </label>
      </RadioGroup>,
    );

    fireEvent.click(screen.getByRole("radio", { name: "Two" }));

    expect(screen.getByRole("radio", { name: "Two" })).toBeChecked();
  });
});
