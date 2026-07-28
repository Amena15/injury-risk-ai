import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../theme/colors';
import TopBar from '../components/TopBar';
import BodyDiagram from '../components/BodyDiagram';
import FactorCard from '../components/FactorCard';
import RecCard from '../components/RecCard';
import PrimaryButton from '../components/Button';

const RISK_CONFIG = {
  Low: { color: colors.low, icon: '✓', label: 'Low risk' },
  Moderate: { color: colors.moderate, icon: '!', label: 'Moderate risk' },
  High: { color: colors.high, icon: '×', label: 'High risk' },
};

export default function ResultsScreen({ result, onBack }) {
  const [openFactor, setOpenFactor] = useState(
    result?.primary_risk_factors?.[0]?.id || null
  );
  const [openRec, setOpenRec] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);

  if (!result) {
    return (
      <SafeAreaView style={styles.emptyContainer}>
        <View style={styles.emptyContent}>
          <Text style={styles.emptyIcon}>Data</Text>
          <Text style={styles.emptyTitle}>No Analysis Data</Text>
          <Text style={styles.emptyMessage}>
            Record or upload a video to get started.
          </Text>
          <PrimaryButton onPress={onBack} style={styles.emptyButton}>
            Back to Camera
          </PrimaryButton>
        </View>
      </SafeAreaView>
    );
  }

  const {
    overall_risk_level = 'Low',
    max_risk_score = 0,
    flagged_joint = 'right_elbow',
    flagged_label,
    primary_risk_factors = [],
    recommendations = [],
    average_metrics = {},
  } = result;

  const risk = RISK_CONFIG[overall_risk_level] || RISK_CONFIG.Low;
  const jointLabel = flagged_label || flagged_joint.replace(/_/g, ' ');

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <TopBar title="Analysis result" onBack={onBack} />

        {/* Verdict Card */}
        <View style={[styles.verdictCard, { borderColor: risk.color + '55', backgroundColor: risk.color + '14' }]}>
          <View style={styles.verdictRow}>
            <View style={styles.verdictIconWrap}>
              <Text style={styles.verdictIcon}>{risk.icon}</Text>
            </View>
            <View style={styles.verdictText}>
              <Text style={[styles.verdictLabel, { color: risk.color }]}>
                {risk.label}
              </Text>
              <Text style={styles.verdictSub}>
                {jointLabel} was the main driver this rep
              </Text>
            </View>
            <Text style={styles.verdictScore}>{max_risk_score}</Text>
          </View>
        </View>

        {/* Body Diagram with flagged joint */}
        <BodyDiagram flag={flagged_joint} />

        {/* Risk Factors */}
        <Text style={styles.sectionTitle}>Why</Text>
        {primary_risk_factors.length > 0 ? (
          primary_risk_factors.map((f) => (
            <FactorCard
              key={f.id}
              item={f}
              open={openFactor === f.id}
              onToggle={() => setOpenFactor(openFactor === f.id ? null : f.id)}
            />
          ))
        ) : (
          <View style={styles.emptySection}>
            <Text style={styles.emptyText}>No specific risk factors identified.</Text>
          </View>
        )}

        {/* Recommendations */}
        <Text style={[styles.sectionTitle, { marginTop: 18 }]}>What to do</Text>
        {recommendations.length > 0 ? (
          recommendations.map((r) => (
            <RecCard
              key={r.id}
              item={r}
              open={openRec === r.id}
              onToggle={() => setOpenRec(openRec === r.id ? null : r.id)}
            />
          ))
        ) : (
          <View style={styles.emptySection}>
            <Text style={styles.emptyText}>No specific recommendations available.</Text>
          </View>
        )}

        {/* Collapsible Metrics */}
        <TouchableOpacity
          onPress={() => setShowMetrics((s) => !s)}
          style={styles.metricsToggle}
        >
          <Text style={styles.metricsToggleText}>
            {showMetrics ? '▲' : '▼'} Joint angle data
          </Text>
        </TouchableOpacity>

        {showMetrics && Object.keys(average_metrics).length > 0 && (
          <View style={styles.metricsPanel}>
            {Object.entries(average_metrics).map(([key, value]) => (
              <View key={key} style={styles.metricRow}>
                <Text style={styles.metricLabel}>
                  {key.replace(/_/g, ' ')}
                </Text>
                <Text style={styles.metricValue}>
                  {typeof value === 'number' ? value.toFixed(1) : value}°
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerIcon}>i</Text>
          <Text style={styles.disclaimerText}>
            Not a medical diagnosis. If you are in pain, see a physiotherapist.
          </Text>
        </View>

        {/* Record Another Button */}
        <View style={styles.footerBtn}>
          <PrimaryButton icon="re" onPress={onBack} tone="ball">
            Record another
          </PrimaryButton>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.ink,
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  emptyContainer: {
    flex: 1,
    backgroundColor: colors.ink,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContent: {
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
    color: colors.chalk,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.chalk,
    marginBottom: 8,
  },
  emptyMessage: {
    fontSize: 16,
    color: colors.chalkDim,
    textAlign: 'center',
    marginBottom: 24,
  },
  emptyButton: {
    minWidth: 200,
  },
  verdictCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  verdictRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    columnGap: 12,
  },
  verdictIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  verdictIcon: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.chalk,
  },
  verdictText: {
    flex: 1,
    minWidth: 0,
  },
  verdictLabel: {
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 32,
  },
  verdictSub: {
    fontSize: 13,
    color: colors.chalkDim,
    marginTop: 4,
    lineHeight: 18,
  },
  verdictScore: {
    fontFamily: 'ui-monospace, SF Mono, JetBrains Mono, Menlo, monospace',
    fontSize: 36,
    fontWeight: '700',
    color: colors.chalk,
    lineHeight: 38,
    marginLeft: 8,
    minWidth: 44,
    textAlign: 'right',
  },
  sectionTitle: {
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: colors.chalkDim,
    fontWeight: '700',
    marginBottom: 10,
  },
  emptySection: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 13.5,
    color: colors.chalkDim,
    fontStyle: 'italic',
  },
  metricsToggle: {
    marginTop: 14,
    paddingVertical: 4,
  },
  metricsToggleText: {
    fontSize: 12.5,
    color: colors.chalkDim,
  },
  metricsPanel: {
    marginTop: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 12,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
  },
  metricLabel: {
    fontFamily: 'ui-monospace, SF Mono, JetBrains Mono, Menlo, monospace',
    fontSize: 11.5,
    color: colors.chalkDim,
    textTransform: 'capitalize',
  },
  metricValue: {
    fontFamily: 'ui-monospace, SF Mono, JetBrains Mono, Menlo, monospace',
    fontSize: 11.5,
    color: colors.chalk,
  },
  disclaimer: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
    marginTop: 18,
  },
  disclaimerIcon: {
    fontSize: 13,
    color: colors.chalkDim,
    marginTop: 1,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 11,
    color: colors.chalkDim,
    lineHeight: 17,
  },
  footerBtn: {
    marginTop: 16,
  },
});
