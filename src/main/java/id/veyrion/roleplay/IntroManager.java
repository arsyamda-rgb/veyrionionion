package id.veyrion.roleplay;

import io.papermc.paper.event.player.AsyncChatEvent;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.event.ClickEvent;
import net.kyori.adventure.text.event.HoverEvent;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextColor;
import net.kyori.adventure.title.Title;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.Registry;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.event.player.PlayerCommandPreprocessEvent;
import org.bukkit.event.player.PlayerDropItemEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerRespawnEvent;
import org.bukkit.event.player.PlayerResourcePackStatusEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import java.time.Duration;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;

/** Seluruh alur pemain baru: menu utama -> gacha ras -> hasil -> masuk dunia. */
public final class IntroManager implements Listener {

    public enum Stage { PACK_WAIT, MENU, DISCORD, SPINNING, RESULT }

    private enum View { MAIN, GACHA, RESULT }

    private static final class GuiHolder implements InventoryHolder {
        final View view;
        Inventory inv;
        GuiHolder(View view) { this.view = view; }
        @Override public Inventory getInventory() { return inv; }
    }

    private static final TextColor GOLD = TextColor.color(0xC9A227);
    private static final int[][] MAIN_BUTTONS = {{28, 34}, {37, 43}, {46, 52}};   // tentukan ras, keluar, discord
    private static final int[] RESULT_BUTTON = {48, 50};

    private final VeyrionPlugin plugin;
    private final RaceStore store;
    private final Map<UUID, Stage> stage = new ConcurrentHashMap<>();
    private final Map<UUID, String> glyphNow = new ConcurrentHashMap<>();
    private final Set<UUID> silent = new HashSet<>();
    private final NamespacedKey uiKey;

    public IntroManager(VeyrionPlugin plugin, RaceStore store) {
        this.plugin = plugin;
        this.store = store;
        this.uiKey = new NamespacedKey(plugin, "ui_item");
    }

    public boolean isFrozen(Player p) { return stage.containsKey(p.getUniqueId()); }

    public Stage stageOf(Player p) { return stage.get(p.getUniqueId()); }

    // ------------------------------------------------------------------ alur

    /** Mulai intro untuk pemain (join pertama atau setelah /veyrion reset). */
    public void begin(Player p) {
        UUID id = p.getUniqueId();
        FileConfiguration c = plugin.getConfig();
        stage.put(id, Stage.PACK_WAIT);

        Location tp = parseLoc(c.getString("intro.teleport", ""));
        if (tp != null) p.teleport(tp);
        if (c.getBoolean("intro.blindness", true)) {
            p.addPotionEffect(new PotionEffect(PotionEffectType.BLINDNESS, PotionEffect.INFINITE_DURATION, 0, false, false, false));
        }
        boolean hasPack = !c.getString("resource-pack.url", "").isBlank();
        long delay = hasPack ? c.getLong("resource-pack.fallback-open-seconds", 20) * 20L : 20L;
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (p.isOnline() && stage.get(id) == Stage.PACK_WAIT) openMain(p);
        }, delay);
    }

    public void openMain(Player p) {
        stage.put(p.getUniqueId(), Stage.MENU);
        open(p, View.MAIN, Glyphs.MAIN);
        p.playSound(p.getLocation(), Sound.BLOCK_ENCHANTMENT_TABLE_USE, 0.6f, 0.8f);
    }

    private void startGacha(Player p) {
        UUID id = p.getUniqueId();
        stage.put(id, Stage.SPINNING);
        open(p, View.GACHA, Glyphs.GACHA_IDLE);
        p.playSound(p.getLocation(), Sound.BLOCK_BEACON_ACTIVATE, 0.5f, 1.4f);

        RaceType result = store.getPending(id);
        if (result == null) {
            result = roll();
            store.setPending(id, result);
        }
        final RaceType fin = result;
        int start = ThreadLocalRandom.current().nextInt(4);
        int n = 20;
        while ((start + n - 1) % 4 != fin.ordinal()) n++;
        final int total = n;
        Bukkit.getScheduler().runTaskLater(plugin, () -> step(p, start, total, 0, fin), 25L);
    }

    private void step(Player p, int start, int n, int k, RaceType result) {
        UUID id = p.getUniqueId();
        if (!p.isOnline() || stage.get(id) != Stage.SPINNING) return;

        if (k < n) {
            setTitle(p, Glyphs.spin((start + k) % 4));
            p.playSound(p.getLocation(), Sound.BLOCK_NOTE_BLOCK_HAT, 0.7f, 0.7f + 0.8f * k / n);
            long delay = k < n - 8 ? 2L : 2L + (long) (k - (n - 8) + 1) * 2L;
            Bukkit.getScheduler().runTaskLater(plugin, () -> step(p, start, n, k + 1, result), delay);
            return;
        }
        setTitle(p, Glyphs.win(result.ordinal()));
        p.playSound(p.getLocation(), Sound.UI_TOAST_CHALLENGE_COMPLETE, 0.8f, 1.0f);
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (!p.isOnline() || stage.get(id) != Stage.SPINNING) return;
            stage.put(id, Stage.RESULT);
            open(p, View.RESULT, Glyphs.result(result.ordinal()));
            p.playSound(p.getLocation(), raceSound(result), 0.9f, 1.0f);
        }, 40L);
    }

    private void finish(Player p) {
        UUID id = p.getUniqueId();
        RaceType race = store.getPending(id);
        if (race == null) race = store.get(id);
        if (race == null) return;

        stage.remove(id);
        glyphNow.remove(id);
        closeSilently(p);
        if (plugin.getConfig().getBoolean("intro.blindness", true)) p.removePotionEffect(PotionEffectType.BLINDNESS);

        store.set(id, race);
        store.setPending(id, null);
        applyPerks(p);

        for (String cmd : plugin.getConfig().getStringList("on-finish-commands")) {
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(),
                    cmd.replace("%player%", p.getName()).replace("%race%", race.key()));
        }
        p.showTitle(Title.title(
                Component.text(plugin.getConfig().getString("messages.finish-title", "Veyrion"), NamedTextColor.WHITE),
                Component.text(plugin.getConfig().getString("messages.finish-subtitle", "Roleplay"), GOLD),
                Title.Times.times(Duration.ofMillis(600), Duration.ofSeconds(3), Duration.ofSeconds(1))));
        p.playSound(p.getLocation(), Sound.ENTITY_PLAYER_LEVELUP, 0.8f, 0.9f);
    }

    private void discord(Player p) {
        stage.put(p.getUniqueId(), Stage.DISCORD);
        closeSilently(p);
        String link = plugin.getConfig().getString("discord-link", "");
        p.sendMessage(Component.text("\n\n"));
        p.sendMessage(Component.text("  Klik di sini untuk membuka Discord Veyrion", GOLD)
                .clickEvent(ClickEvent.openUrl(link))
                .hoverEvent(HoverEvent.showText(Component.text(link, NamedTextColor.GRAY))));
        p.sendMessage(Component.text("  [ Kembali ke menu ]", NamedTextColor.WHITE)
                .clickEvent(ClickEvent.runCommand("/veyrion menu"))
                .hoverEvent(HoverEvent.showText(Component.text("Buka menu lagi", NamedTextColor.GRAY))));
    }

    // ------------------------------------------------------------------ GUI helper

    private void open(Player p, View view, String glyph) {
        GuiHolder h = new GuiHolder(view);
        Inventory inv = Bukkit.createInventory(h, 54, Component.text(Glyphs.title(glyph), NamedTextColor.WHITE));
        h.inv = inv;
        int[][] zones = switch (view) {
            case MAIN -> MAIN_BUTTONS;
            case RESULT -> new int[][]{RESULT_BUTTON};
            default -> new int[0][];
        };
        ItemStack blank = blank();
        for (int[] z : zones) for (int i = z[0]; i <= z[1]; i++) inv.setItem(i, blank.clone());

        glyphNow.put(p.getUniqueId(), glyph);
        silent.add(p.getUniqueId());
        try {
            p.openInventory(inv);
        } finally {
            silent.remove(p.getUniqueId());
        }
        giveCursor(p);
    }

    @SuppressWarnings("deprecation")
    private void setTitle(Player p, String glyph) {
        glyphNow.put(p.getUniqueId(), glyph);
        if (p.getOpenInventory().getTopInventory().getHolder() instanceof GuiHolder) {
            p.getOpenInventory().setTitle("\u00A7f" + Glyphs.title(glyph));
            giveCursor(p);
        }
    }

    private void closeSilently(Player p) {
        clearCursor(p);
        silent.add(p.getUniqueId());
        try {
            p.closeInventory();
        } finally {
            silent.remove(p.getUniqueId());
        }
    }

    @SuppressWarnings("deprecation")
    private ItemStack blank() {
        ItemStack it = new ItemStack(org.bukkit.Material.PAPER);
        ItemMeta m = it.getItemMeta();
        m.setCustomModelData(1);
        m.setHideTooltip(true);
        m.getPersistentDataContainer().set(uiKey, PersistentDataType.BYTE, (byte) 1);
        it.setItemMeta(m);
        return it;
    }

    // ------------------------------------------------------------------ kursor buatan

    private boolean cursorOn() { return plugin.getConfig().getBoolean("cursor.enabled", true); }

    @SuppressWarnings("deprecation")
    private ItemStack cursorItem() {
        ItemStack it = new ItemStack(org.bukkit.Material.PAPER);
        ItemMeta m = it.getItemMeta();
        m.setCustomModelData(2);
        m.setHideTooltip(true);
        m.getPersistentDataContainer().set(uiKey, PersistentDataType.BYTE, (byte) 1);
        it.setItemMeta(m);
        return it;
    }

    /** Item yang tampil di posisi mouse = kursor buatan. Dipasang 1 tick setelah GUI terbuka. */
    private void giveCursor(Player p) {
        if (!cursorOn()) return;
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (p.isOnline() && p.getOpenInventory().getTopInventory().getHolder() instanceof GuiHolder) {
                p.setItemOnCursor(cursorItem());
            }
        }, 1L);
    }

    private void clearCursor(Player p) {
        if (!cursorOn()) return;
        ItemStack cur = p.getItemOnCursor();
        if (isUiItem(cur)) p.setItemOnCursor(null);
    }

    private boolean isUiItem(ItemStack it) {
        if (it == null || !it.hasItemMeta()) return false;
        return it.getItemMeta().getPersistentDataContainer().has(uiKey, PersistentDataType.BYTE);
    }

    /** Buang item UI yang mungkin nyangkut di inventory (misal setelah crash). */
    private void stripUiItems(Player p) {
        ItemStack[] c = p.getInventory().getContents();
        for (int i = 0; i < c.length; i++) {
            if (isUiItem(c[i])) p.getInventory().setItem(i, null);
        }
        clearCursor(p);
    }

    // ------------------------------------------------------------------ gacha & perks

    private RaceType roll() {
        double[] w = new double[4];
        double total = 0;
        for (RaceType r : RaceType.values()) {
            w[r.ordinal()] = Math.max(0, plugin.getConfig().getDouble("races." + r.key() + ".weight", 25));
            total += w[r.ordinal()];
        }
        if (total <= 0) return RaceType.values()[ThreadLocalRandom.current().nextInt(4)];
        double x = ThreadLocalRandom.current().nextDouble() * total;
        for (RaceType r : RaceType.values()) {
            x -= w[r.ordinal()];
            if (x < 0) return r;
        }
        return RaceType.HUMAN;
    }

    private Sound raceSound(RaceType r) {
        return switch (r) {
            case ELF -> Sound.ENTITY_EVOKER_PREPARE_SUMMON;
            case BEAST -> Sound.ENTITY_WOLF_HOWL;
            case HUMAN -> Sound.ITEM_ARMOR_EQUIP_IRON;
            case DRAGON -> Sound.ENTITY_ENDER_DRAGON_GROWL;
        };
    }

    public void applyPerks(Player p) {
        RaceType r = store.get(p.getUniqueId());
        if (r == null) return;
        for (String s : plugin.getConfig().getStringList("races." + r.key() + ".effects")) {
            PotionEffectType type = parseEffect(s);
            if (type == null) continue;
            int amp = 0;
            String[] a = s.split(":");
            if (a.length > 1) {
                try { amp = Integer.parseInt(a[1].trim()); } catch (NumberFormatException ignored) { }
            }
            PotionEffect cur = p.getPotionEffect(type);
            if (cur == null || cur.getAmplifier() != amp || !cur.isInfinite()) {
                p.addPotionEffect(new PotionEffect(type, PotionEffect.INFINITE_DURATION, amp, false, false, true));
            }
        }
    }

    public void clearPerks(Player p) {
        for (RaceType r : RaceType.values()) {
            for (String s : plugin.getConfig().getStringList("races." + r.key() + ".effects")) {
                PotionEffectType type = parseEffect(s);
                if (type != null) p.removePotionEffect(type);
            }
        }
    }

    public void refreshPerks() {
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (!isFrozen(p)) applyPerks(p);
        }
    }

    private PotionEffectType parseEffect(String s) {
        String name = s.split(":")[0].trim().toLowerCase().replace(' ', '_');
        NamespacedKey key = NamespacedKey.minecraft(name);
        PotionEffectType t = Registry.POTION_EFFECT_TYPE.get(key);
        if (t == null) plugin.getLogger().warning("Potion effect tidak dikenal di config: " + s);
        return t;
    }

    // ------------------------------------------------------------------ util

    private Location parseLoc(String s) {
        if (s == null || s.isBlank()) return null;
        try {
            String[] a = s.split(",");
            World w = Bukkit.getWorld(a[0].trim());
            if (w == null) return null;
            return new Location(w, Double.parseDouble(a[1].trim()), Double.parseDouble(a[2].trim()), Double.parseDouble(a[3].trim()),
                    a.length > 4 ? Float.parseFloat(a[4].trim()) : 0f, a.length > 5 ? Float.parseFloat(a[5].trim()) : 0f);
        } catch (Exception e) {
            plugin.getLogger().warning("intro.teleport tidak valid: " + s);
            return null;
        }
    }

    private void sendPack(Player p) {
        FileConfiguration c = plugin.getConfig();
        String url = c.getString("resource-pack.url", "");
        if (url == null || url.isBlank()) return;
        byte[] hash = null;
        String sha = c.getString("resource-pack.sha1", "");
        if (sha != null && !sha.isBlank()) {
            try {
                hash = HexFormat.of().parseHex(sha.trim());
            } catch (IllegalArgumentException ex) {
                plugin.getLogger().warning("resource-pack.sha1 tidak valid, dikirim tanpa hash.");
            }
        }
        p.setResourcePack(url, hash, Component.text(c.getString("resource-pack.prompt", "")), c.getBoolean("resource-pack.required", true));
    }

    // ------------------------------------------------------------------ events

    @EventHandler
    public void onJoin(PlayerJoinEvent e) {
        Player p = e.getPlayer();
        stripUiItems(p);
        sendPack(p);
        UUID id = p.getUniqueId();
        if (store.get(id) != null) {
            Bukkit.getScheduler().runTaskLater(plugin, () -> applyPerks(p), 20L);
            return;
        }
        begin(p);
    }

    @EventHandler
    public void onPackStatus(PlayerResourcePackStatusEvent e) {
        Player p = e.getPlayer();
        if (e.getStatus() != PlayerResourcePackStatusEvent.Status.SUCCESSFULLY_LOADED) return;
        if (stage.get(p.getUniqueId()) != Stage.PACK_WAIT) return;
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (p.isOnline() && stage.get(p.getUniqueId()) == Stage.PACK_WAIT) openMain(p);
        }, 10L);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        Player p = e.getPlayer();
        UUID id = p.getUniqueId();
        clearCursor(p);
        if (stage.remove(id) != null && plugin.getConfig().getBoolean("intro.blindness", true)) {
            p.removePotionEffect(PotionEffectType.BLINDNESS);
        }
        glyphNow.remove(id);
        silent.remove(id);
    }

    @EventHandler
    public void onRespawn(PlayerRespawnEvent e) {
        Player p = e.getPlayer();
        Bukkit.getScheduler().runTaskLater(plugin, () -> applyPerks(p), 2L);
    }

    @EventHandler
    public void onClick(InventoryClickEvent e) {
        if (!(e.getView().getTopInventory().getHolder() instanceof GuiHolder h)) return;
        e.setCancelled(true);
        if (!(e.getWhoClicked() instanceof Player p)) return;
        if (e.getClickedInventory() != e.getView().getTopInventory()) return;
        int s = e.getRawSlot();
        Stage st = stage.get(p.getUniqueId());

        if (h.view == View.MAIN && st == Stage.MENU) {
            if (inRange(s, MAIN_BUTTONS[0])) {
                startGacha(p);
            } else if (inRange(s, MAIN_BUTTONS[1])) {
                stage.remove(p.getUniqueId());
                p.kick(Component.text(plugin.getConfig().getString("messages.kick-exit", "Sampai jumpa di dunia Veyrion.")));
            } else if (inRange(s, MAIN_BUTTONS[2])) {
                discord(p);
            }
        } else if (h.view == View.RESULT && st == Stage.RESULT && inRange(s, RESULT_BUTTON)) {
            finish(p);
        }
    }

    private boolean inRange(int s, int[] r) { return s >= r[0] && s <= r[1]; }

    @EventHandler
    public void onDrag(InventoryDragEvent e) {
        if (e.getView().getTopInventory().getHolder() instanceof GuiHolder) e.setCancelled(true);
    }

    @EventHandler
    public void onClose(InventoryCloseEvent e) {
        if (!(e.getInventory().getHolder() instanceof GuiHolder h)) return;
        if (!(e.getPlayer() instanceof Player p)) return;
        UUID id = p.getUniqueId();
        clearCursor(p);   // harus sebelum vanilla mengembalikan item kursor ke inventory pemain
        if (silent.contains(id)) return;
        Stage st = stage.get(id);
        if (st == null || st == Stage.DISCORD || st == Stage.PACK_WAIT) return;
        // pemain menutup GUI (ESC) -> buka lagi, tidak bisa kabur dari intro
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (!p.isOnline() || stage.get(id) != st) return;
            if (p.getOpenInventory().getTopInventory().getHolder() instanceof GuiHolder) return;
            String g = glyphNow.getOrDefault(id, Glyphs.MAIN);
            open(p, h.view, g);
        }, 1L);
    }

    @EventHandler
    public void onMove(PlayerMoveEvent e) {
        if (!isFrozen(e.getPlayer()) || e.getTo() == null) return;
        Location f = e.getFrom();
        Location t = e.getTo();
        if (f.getX() != t.getX() || f.getY() != t.getY() || f.getZ() != t.getZ()) {
            Location keep = f.clone();
            keep.setYaw(t.getYaw());
            keep.setPitch(t.getPitch());
            e.setTo(keep);
        }
    }

    @EventHandler
    public void onDamage(EntityDamageEvent e) {
        if (e.getEntity() instanceof Player p && isFrozen(p)) e.setCancelled(true);
    }

    @EventHandler
    public void onInteract(PlayerInteractEvent e) {
        if (isFrozen(e.getPlayer())) e.setCancelled(true);
    }

    @EventHandler
    public void onDrop(PlayerDropItemEvent e) {
        if (isFrozen(e.getPlayer())) e.setCancelled(true);
    }

    @EventHandler
    public void onBreak(BlockBreakEvent e) {
        if (isFrozen(e.getPlayer())) e.setCancelled(true);
    }

    @EventHandler
    public void onPlace(BlockPlaceEvent e) {
        if (isFrozen(e.getPlayer())) e.setCancelled(true);
    }

    @EventHandler
    public void onChat(AsyncChatEvent e) {
        if (isFrozen(e.getPlayer())) e.setCancelled(true);
    }

    @EventHandler
    public void onCommand(PlayerCommandPreprocessEvent e) {
        if (!isFrozen(e.getPlayer())) return;
        String m = e.getMessage().toLowerCase().trim();
        if (!m.equals("/veyrion menu")) e.setCancelled(true);
    }
}
