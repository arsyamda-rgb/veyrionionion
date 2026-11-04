package id.veyrion.roleplay;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.OfflinePlayer;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class VeyrionCommand implements CommandExecutor, TabCompleter {

    private final VeyrionPlugin plugin;
    private final RaceStore store;
    private final IntroManager intro;

    public VeyrionCommand(VeyrionPlugin plugin, RaceStore store, IntroManager intro) {
        this.plugin = plugin;
        this.store = store;
        this.intro = intro;
    }

    private void msg(CommandSender s, String text) {
        s.sendMessage(Component.text(text, NamedTextColor.GRAY));
    }

    @Override
    public boolean onCommand(CommandSender sender, Command cmd, String label, String[] args) {
        if (cmd.getName().equalsIgnoreCase("ras")) {
            if (!(sender instanceof Player p)) { msg(sender, "Hanya untuk pemain."); return true; }
            RaceType r = store.get(p.getUniqueId());
            msg(sender, r == null ? "Kamu belum menentukan ras." : "Rasmu: " + r.display());
            return true;
        }
        if (args.length == 0) { msg(sender, "/veyrion <menu|reload|reset|set|info>"); return true; }

        switch (args[0].toLowerCase(Locale.ROOT)) {
            case "menu" -> {
                if (sender instanceof Player p && intro.stageOf(p) == IntroManager.Stage.DISCORD) intro.openMain(p);
            }
            case "reload" -> {
                if (!admin(sender)) return true;
                plugin.reloadConfig();
                msg(sender, "Config dimuat ulang.");
            }
            case "reset" -> {
                if (!admin(sender) || args.length < 2) { if (args.length < 2) msg(sender, "/veyrion reset <player>"); return true; }
                OfflinePlayer t = target(args[1]);
                store.set(t.getUniqueId(), null);
                store.setPending(t.getUniqueId(), null);
                Player on = t.getPlayer();
                if (on != null) { intro.clearPerks(on); intro.begin(on); }
                msg(sender, "Ras " + args[1] + " direset.");
            }
            case "set" -> {
                if (!admin(sender)) return true;
                RaceType r = args.length > 2 ? RaceType.parse(args[2]) : null;
                if (args.length < 3 || r == null) { msg(sender, "/veyrion set <player> <elf|beast|human|dragon>"); return true; }
                OfflinePlayer t = target(args[1]);
                store.set(t.getUniqueId(), r);
                store.setPending(t.getUniqueId(), null);
                Player on = t.getPlayer();
                if (on != null) { intro.clearPerks(on); intro.applyPerks(on); }
                msg(sender, args[1] + " sekarang ras " + r.display() + ".");
            }
            case "info" -> {
                if (!admin(sender) || args.length < 2) return true;
                RaceType r = store.get(target(args[1]).getUniqueId());
                msg(sender, args[1] + ": " + (r == null ? "belum punya ras" : r.display()));
            }
            default -> msg(sender, "/veyrion <menu|reload|reset|set|info>");
        }
        return true;
    }

    private boolean admin(CommandSender s) {
        if (s.hasPermission("veyrion.admin")) return true;
        msg(s, "Kamu tidak punya izin.");
        return false;
    }

    @SuppressWarnings("deprecation")
    private OfflinePlayer target(String name) {
        Player on = Bukkit.getPlayerExact(name);
        return on != null ? on : Bukkit.getOfflinePlayer(name);
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command cmd, String alias, String[] args) {
        List<String> out = new ArrayList<>();
        if (args.length == 1) {
            for (String s : List.of("menu", "reload", "reset", "set", "info")) if (s.startsWith(args[0].toLowerCase(Locale.ROOT))) out.add(s);
        } else if (args.length == 2 && !args[0].equalsIgnoreCase("menu") && !args[0].equalsIgnoreCase("reload")) {
            for (Player p : Bukkit.getOnlinePlayers()) if (p.getName().toLowerCase(Locale.ROOT).startsWith(args[1].toLowerCase(Locale.ROOT))) out.add(p.getName());
        } else if (args.length == 3 && args[0].equalsIgnoreCase("set")) {
            for (RaceType r : RaceType.values()) if (r.key().startsWith(args[2].toLowerCase(Locale.ROOT))) out.add(r.key());
        }
        return out;
    }
}
