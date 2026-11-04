package id.veyrion.roleplay;

public enum RaceType {
    ELF("Elf"), BEAST("Beast"), HUMAN("Human"), DRAGON("Dragon");

    private final String display;

    RaceType(String display) { this.display = display; }

    public String display() { return display; }

    public String key() { return name().toLowerCase(); }

    public static RaceType parse(String s) {
        if (s == null) return null;
        for (RaceType r : values()) if (r.name().equalsIgnoreCase(s)) return r;
        return null;
    }
}
