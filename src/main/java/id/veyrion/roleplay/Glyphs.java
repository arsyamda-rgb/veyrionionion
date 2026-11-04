package id.veyrion.roleplay;

/** Karakter private-use yang dipetakan ke gambar GUI di resource pack (assets/minecraft/font/default.json). */
public final class Glyphs {
    private Glyphs() {}

    public static final String SHIFT = "\uF808";           // geser -8px supaya gambar pas di tepi GUI
    // Latar FULL LAYAR (1920x1080 gui px, 1 gambar dipakai semua layar):
    //  Urutan title: SHIFT_BG -> BG -> SHIFT_BACK -> gambar panel. Hitungan: (1920-176)/2 = 872 offset kiri latar;
    //  awal -(8+872) = -880; setelah latar maju 1920+1, balik ke tepi chest = 872-1921 = -1049.
    public static final String SHIFT_BG = "\uF809";        // -880
    public static final String BG = "\uE00E";
    // Logo di sebelah kanan judul (semua layar): panel maju 177 -> geser -3 -> logo (tepi kiri terlihat = chest kiri + 180)
    public static final String SHIFT_LOGO = "\uF80B";      // -3
    public static final String LOGO = "\uE00F";
    public static final String SHIFT_BACK = "\uF80A";      // -1049 (lebar latar 1920 + 1 advance, dikurangi offset 872)
    public static final String MAIN = "\uE000";
    public static final String GACHA_IDLE = "\uE001";

    public static String spin(int i) { return String.valueOf((char) (0xE002 + i)); }
    public static String win(int i) { return String.valueOf((char) (0xE006 + i)); }
    public static String result(int i) { return String.valueOf((char) (0xE00A + i)); }

    public static String title(String glyph) {
        return SHIFT_BG + BG + SHIFT_BACK + glyph + SHIFT_LOGO + LOGO;   // logo tampil di semua layar
    }
}
